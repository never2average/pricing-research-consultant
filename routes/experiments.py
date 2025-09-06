import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from datastore.models import PricingExperimentRequest, PricingExperimentRuns, Product
from logical_functions.workflow_manager import start_experiment_workflow
from logical_functions.experiment_run_manager import get_latest_experiment_run

router = APIRouter()

@router.post("/experiments/")
async def create_experiment(
    product_id: str,
    objective: str,
    usecase: str
):
    try:
        product = Product.objects(id=product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        last_experiment = PricingExperimentRequest.objects().order_by('-experiment_number').first()
        next_experiment_number = (last_experiment.experiment_number + 1) if last_experiment else 1

        experiment_request = PricingExperimentRequest(
            product=product,
            experiment_number=next_experiment_number,
            objective=objective,
            usecase=usecase,
            experiment_gen_stage="product_context_initialized",
            created_on=datetime.now(timezone.utc)
        )
        experiment_request.save()

        asyncio.create_task(
            asyncio.to_thread(start_experiment_workflow, experiment_request)
        )
        return {"message": "Experiment created successfully", "id": str(experiment_request.id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiments")
async def get_experiments_by_stage(stage: str = None, experiment_number: int = None):
    try:
        if experiment_number and stage:
            experiment_request = PricingExperimentRequest.objects(experiment_number=experiment_number).first()
            if not experiment_request:
                return {"experiments": []}
            
            experiment_run = PricingExperimentRuns.objects(
                experiment_request=experiment_request,
                experiment_gen_stage=stage
            ).first()
            if not experiment_run:
                return {"experiments": []}
            experiments = [experiment_run]
            
        elif stage:
            experiment_runs = PricingExperimentRuns.objects(experiment_gen_stage=stage)
            return {"experiments": [run.experiment_request.experiment_number for run in experiment_runs]}
            
        elif experiment_number:
            experiment_request = PricingExperimentRequest.objects(experiment_number=experiment_number).first()
            if not experiment_request:
                return {"experiments": []}
            experiment_runs = PricingExperimentRuns.objects(experiment_request=experiment_request)
            return {"experiments": [run.experiment_gen_stage for run in experiment_runs]}
        else:
            raise HTTPException(status_code=400, detail="Either stage or experiment_number parameter is required")

        return {
            "experiments": [
                {
                    "run_id": str(exp.id),
                    "request_id": str(exp.experiment_request.id),
                    "product": exp.experiment_request.product.product_name,
                    "product_id": str(exp.experiment_request.product.id),
                    "experiment_number": exp.experiment_request.experiment_number,
                    "experiment_gen_stage": exp.experiment_gen_stage,
                    "request_gen_stage": exp.experiment_request.experiment_gen_stage if exp.experiment_request.experiment_gen_stage else None,
                    "objective": exp.experiment_request.objective if exp.experiment_request.objective else None,
                    "usecase": exp.experiment_request.usecase if exp.experiment_request.usecase else None,
                    "positioning_summary": exp.positioning_summary if exp.positioning_summary else None,
                    "usage_summary": exp.usage_summary if exp.usage_summary else None,
                    "roi_gaps": exp.roi_gaps if exp.roi_gaps else None,
                    "experimental_pricing_plan": exp.experimental_pricing_plan if exp.experimental_pricing_plan else None,
                    "simulation_result": exp.simulation_result if exp.simulation_result else None,
                    "usage_projections": [
                        {
                            "usage_value_in_units": proj.usage_value_in_units,
                            "usage_unit": proj.usage_unit,
                            "target_date": str(proj.target_date) if proj.target_date else None
                        } for proj in exp.usage_projections
                    ] if exp.usage_projections else None,
                    "revenue_projections": [
                        {
                            "usage_value_in_units": proj.usage_value_in_units,
                            "usage_unit": proj.usage_unit,
                            "target_date": str(proj.target_date) if proj.target_date else None
                        } for proj in exp.revenue_projections
                    ] if exp.revenue_projections else None,
                    "cashflow_feasibility_comments": exp.cashflow_feasibility_comments if exp.cashflow_feasibility_comments else None,
                    "cashflow_no_negative_impact_approval_given": exp.cashflow_no_negative_impact_approval_given,
                    "experiment_feedback_summary": exp.experiment_feedback_summary if exp.experiment_feedback_summary else None,
                    "experiment_is_deployed": exp.experiment_is_deployed,
                    "experiment_deployed_on": str(exp.experiment_deployed_on) if exp.experiment_deployed_on else None,
                    "run_created_on": str(exp.created_on) if exp.created_on else None,
                    "request_created_on": str(exp.experiment_request.created_on) if exp.experiment_request.created_on else None,
                    "relevant_segments": [
                        {
                            "segment_name": seg.segment_name,
                            "segment_cdp_uid": seg.segment_cdp_uid,
                            "segment_description": seg.segment_description,
                            "segment_filter_logic": seg.segment_filter_logic,
                            "segment_usage_summary": seg.segment_usage_summary,
                            "segment_revenue_attribution_summary": seg.segment_revenue_attribution_summary
                        } for seg in exp.relevant_segments
                    ] if exp.relevant_segments else None
                } for exp in experiments
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiments/all-runs/{experiment_number}")
async def get_all_experiment_runs(experiment_number: int):
    try:
        experiment_request = PricingExperimentRequest.objects(experiment_number=experiment_number).first()
        if not experiment_request:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        all_runs = PricingExperimentRuns.objects(experiment_request=experiment_request).order_by('created_on')
        
        runs_data = []
        for run in all_runs:
            runs_data.append({
                "run_id": str(run.id),
                "experiment_gen_stage": run.experiment_gen_stage,
                "positioning_summary": run.positioning_summary,
                "usage_summary": run.usage_summary,
                "roi_gaps": run.roi_gaps,
                "experimental_pricing_plan": run.experimental_pricing_plan,
                "simulation_result": run.simulation_result,
                "usage_projections": [
                    {
                        "usage_value_in_units": proj.usage_value_in_units,
                        "usage_unit": proj.usage_unit,
                        "target_date": str(proj.target_date) if proj.target_date else None
                    } for proj in run.usage_projections
                ] if run.usage_projections else None,
                "revenue_projections": [
                    {
                        "usage_value_in_units": proj.usage_value_in_units,
                        "usage_unit": proj.usage_unit,
                        "target_date": str(proj.target_date) if proj.target_date else None
                    } for proj in run.revenue_projections
                ] if run.revenue_projections else None,
                "cashflow_feasibility_comments": run.cashflow_feasibility_comments,
                "experiment_feedback_summary": run.experiment_feedback_summary,
                "created_on": str(run.created_on) if run.created_on else None
            })
        
        latest_completed_run = get_latest_experiment_run(experiment_request, "completed")
        
        return {
            "experiment_number": experiment_number,
            "request_id": str(experiment_request.id),
            "product_name": experiment_request.product.product_name,
            "request_gen_stage": experiment_request.experiment_gen_stage if experiment_request.experiment_gen_stage else None,
            "objective": experiment_request.objective,
            "usecase": experiment_request.usecase,
            "cashflow_approval_given": latest_completed_run.cashflow_no_negative_impact_approval_given if latest_completed_run else None,
            "is_deployed": latest_completed_run.experiment_is_deployed if latest_completed_run else None,
            "deployed_on": str(latest_completed_run.experiment_deployed_on) if latest_completed_run and latest_completed_run.experiment_deployed_on else None,
            "all_runs": runs_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
