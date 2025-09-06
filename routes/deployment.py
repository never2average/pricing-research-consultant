from fastapi import APIRouter, HTTPException
from datastore.models import PricingExperimentRequest
from logical_functions.experiment_utils import get_completed_experiments_for_deployment
from logical_functions.experiment_run_manager import get_latest_experiment_run

router = APIRouter()

@router.get("/experiments/ready-for-deployment")
async def get_experiments_ready_for_deployment():
    try:
        ready_experiments = get_completed_experiments_for_deployment()
        
        experiments_data = []
        for experiment_request in ready_experiments:
            latest_completed_run = get_latest_experiment_run(experiment_request, "completed")
            if latest_completed_run:
                experiments_data.append({
                    "request_id": str(experiment_request.id),
                    "experiment_number": experiment_request.experiment_number,
                    "product_name": experiment_request.product.product_name,
                    "product_id": str(experiment_request.product.id),
                    "objective": experiment_request.objective,
                    "usecase": experiment_request.usecase,
                    "experimental_pricing_plan": latest_completed_run.experimental_pricing_plan,
                    "cashflow_feasibility_comments": latest_completed_run.cashflow_feasibility_comments,
                    "cashflow_approval_given": latest_completed_run.cashflow_no_negative_impact_approval_given,
                    "completed_on": str(latest_completed_run.created_on) if latest_completed_run.created_on else None
                })
        
        return {"ready_for_deployment": experiments_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/experiments/{experiment_number}/deploy")
async def deploy_pricing_experiment(experiment_number: int):
    try:
        from datetime import datetime, timezone
        
        experiment_request = PricingExperimentRequest.objects(experiment_number=experiment_number).first()
        if not experiment_request:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        latest_completed_run = get_latest_experiment_run(experiment_request, "completed")
        if not latest_completed_run:
            raise HTTPException(
                status_code=400, 
                detail="No completed experiment run found for deployment"
            )
        
        if not latest_completed_run.cashflow_no_negative_impact_approval_given:
            raise HTTPException(
                status_code=400, 
                detail="Cannot deploy experiment: cashflow negative impact approval not given"
            )
        
        if latest_completed_run.experiment_is_deployed:
            raise HTTPException(
                status_code=400, 
                detail="Experiment already deployed"
            )
        
        if not latest_completed_run.experimental_pricing_plan:
            raise HTTPException(
                status_code=400, 
                detail="No experimental pricing plan available for deployment"
            )
        
        deployment_data = {
            "product_id": str(experiment_request.product.id),
            "product_name": experiment_request.product.product_name,
            "experiment_number": experiment_request.experiment_number,
            "pricing_plan": latest_completed_run.experimental_pricing_plan,
            "objective": experiment_request.objective,
            "usecase": experiment_request.usecase,
            "cashflow_comments": latest_completed_run.cashflow_feasibility_comments,
            "usage_projections": [
                {
                    "usage_value_in_units": proj.usage_value_in_units,
                    "usage_unit": proj.usage_unit,
                    "target_date": str(proj.target_date) if proj.target_date else None
                } for proj in latest_completed_run.usage_projections
            ] if latest_completed_run.usage_projections else None,
            "revenue_projections": [
                {
                    "usage_value_in_units": proj.usage_value_in_units,
                    "usage_unit": proj.usage_unit,
                    "target_date": str(proj.target_date) if proj.target_date else None
                } for proj in latest_completed_run.revenue_projections
            ] if latest_completed_run.revenue_projections else None
        }
        
        latest_completed_run.experiment_is_deployed = True
        latest_completed_run.experiment_deployed_on = datetime.now(timezone.utc)
        latest_completed_run.save()
        
        return {
            "message": f"Experiment {experiment_number} successfully deployed",
            "deployment_data": deployment_data,
            "deployed_on": str(latest_completed_run.experiment_deployed_on)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
