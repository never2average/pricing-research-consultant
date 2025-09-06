from fastapi import FastAPI, HTTPException
from datastore.models import PricingExperiment, Product

app = FastAPI()

@app.post("/experiments/")
async def create_experiment(
    product_id: str,
    experiment_number: int,
    objective: str,
    usecase: str
):
    try:
        product = Product.objects(id=product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            

        experiment = PricingExperiment(
            product=product,
            experiment_number=experiment_number,
            experiment_gen_stage="segments_loaded",
            objective=objective,
            usecase=usecase,
        )
        experiment.save()
        
        return {"message": "Experiment created successfully", "id": str(experiment.id)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/experiments/{stage}")
async def get_experiments_by_stage(stage: str):
    try:
        experiments = PricingExperiment.objects(experiment_gen_stage=stage)
        return {
            "experiments": [
                {
                    "id": str(exp.id),
                    "product": exp.product.product_name,
                    "product_id": str(exp.product.id),
                    "experiment_number": exp.experiment_number,
                    "experiment_gen_stage": exp.experiment_gen_stage,
                    "objective": exp.objective if exp.objective else None,
                    "usecase": exp.usecase if exp.usecase else None,
                    "positioning_summary": exp.positioning_summary if exp.positioning_summary else None,
                    "usage_summary": exp.usage_summary if exp.usage_summary else None,
                    "roi_gaps": exp.roi_gaps if exp.roi_gaps else None,
                    "experimental_pricing_plan": exp.experimental_pricing_plan if exp.experimental_pricing_plan else None,
                    "simulation_result": exp.simulation_result if exp.simulation_result else None,
                    "cashflow_feasibility_comments": exp.cashflow_feasibility_comments if exp.cashflow_feasibility_comments else None,
                    "experiment_feedback_summary": exp.experiment_feedback_summary if exp.experiment_feedback_summary else None,
                    "experiment_is_deployed": str(exp.experiment_is_deployed) if exp.experiment_is_deployed else None,
                    "experiment_deployed_on": str(exp.experiment_deployed_on) if exp.experiment_deployed_on else None
                } for exp in experiments
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
