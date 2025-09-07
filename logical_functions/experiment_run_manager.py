from datetime import datetime, timezone
from typing import List, Optional
from datastore.types import PricingExperimentPydantic
from datastore.models import PricingExperimentRequest, PricingExperimentRuns

def create_initial_experiment_run(experiment_request: PricingExperimentRequest, stage: str):
    initial_run = PricingExperimentRuns(
        experiment_request=experiment_request,
        experiment_gen_stage=stage,
        created_on=datetime.now(timezone.utc)
    )
    initial_run.save()
    print(f"Initial experiment run created for experiment {experiment_request.experiment_number}: {stage}")
    return initial_run

def create_experiment_run(experiment_request: PricingExperimentRequest, updated_data: Optional[List[PricingExperimentPydantic]], stage: str):
    data = updated_data[0] if updated_data else None
    
    new_run = PricingExperimentRuns(
        experiment_request=experiment_request,
        experiment_gen_stage=stage,
        created_on=datetime.now(timezone.utc)
    )
    
    if data:
        new_run.positioning_summary = data.positioning_summary if hasattr(data, 'positioning_summary') else None
        new_run.usage_summary = data.usage_summary if hasattr(data, 'usage_summary') else None
        new_run.roi_gaps = data.roi_gaps if hasattr(data, 'roi_gaps') else None
        new_run.experimental_pricing_plan = data.experimental_pricing_plan if hasattr(data, 'experimental_pricing_plan') else None
        new_run.simulation_result = data.simulation_result if hasattr(data, 'simulation_result') else None
        new_run.cashflow_feasibility_comments = data.cashflow_feasibility_comments if hasattr(data, 'cashflow_feasibility_comments') else None
        new_run.usage_projections = data.usage_projections if hasattr(data, 'usage_projections') else None
        new_run.revenue_projections = data.revenue_projections if hasattr(data, 'revenue_projections') else None
        new_run.experiment_feedback_summary = data.experiment_feedback_summary if hasattr(data, 'experiment_feedback_summary') else None
        new_run.relevant_segment = data.relevant_segment if hasattr(data, 'relevant_segment') else None
        new_run.cashflow_no_negative_impact_approval_given = data.cashflow_no_negative_impact_approval_given if hasattr(data, 'cashflow_no_negative_impact_approval_given') else None
        new_run.experiment_is_deployed = data.experiment_is_deployed if hasattr(data, 'experiment_is_deployed') else None
        new_run.experiment_deployed_on = data.experiment_deployed_on if hasattr(data, 'experiment_deployed_on') else None
    
    new_run.save()
    print(f"Experiment run created for experiment {experiment_request.experiment_number}: {stage}")
    return new_run

def update_current_experiment_run(current_run: PricingExperimentRuns, updated_data: Optional[List[PricingExperimentPydantic]]):
    data = updated_data[0] if updated_data else None
    
    if data:
        current_run.positioning_summary = data.positioning_summary if hasattr(data, 'positioning_summary') else current_run.positioning_summary
        current_run.usage_summary = data.usage_summary if hasattr(data, 'usage_summary') else current_run.usage_summary
        current_run.roi_gaps = data.roi_gaps if hasattr(data, 'roi_gaps') else current_run.roi_gaps
        current_run.experimental_pricing_plan = data.experimental_pricing_plan if hasattr(data, 'experimental_pricing_plan') else current_run.experimental_pricing_plan
        current_run.simulation_result = data.simulation_result if hasattr(data, 'simulation_result') else current_run.simulation_result
        current_run.cashflow_feasibility_comments = data.cashflow_feasibility_comments if hasattr(data, 'cashflow_feasibility_comments') else current_run.cashflow_feasibility_comments
        current_run.usage_projections = data.usage_projections if hasattr(data, 'usage_projections') else current_run.usage_projections
        current_run.revenue_projections = data.revenue_projections if hasattr(data, 'revenue_projections') else current_run.revenue_projections
        current_run.experiment_feedback_summary = data.experiment_feedback_summary if hasattr(data, 'experiment_feedback_summary') else current_run.experiment_feedback_summary
        current_run.cashflow_no_negative_impact_approval_given = data.cashflow_no_negative_impact_approval_given if hasattr(data, 'cashflow_no_negative_impact_approval_given') else current_run.cashflow_no_negative_impact_approval_given
        current_run.experiment_is_deployed = data.experiment_is_deployed if hasattr(data, 'experiment_is_deployed') else current_run.experiment_is_deployed
        current_run.experiment_deployed_on = data.experiment_deployed_on if hasattr(data, 'experiment_deployed_on') else current_run.experiment_deployed_on
    
    current_run.save()
    print(f"Experiment run updated for experiment {current_run.experiment_request.experiment_number}")
    return current_run

def get_latest_experiment_run(experiment_request: PricingExperimentRequest, stage: str = None):
    query = {"experiment_request": experiment_request}
    if stage:
        query["experiment_gen_stage"] = stage
    
    return PricingExperimentRuns.objects(**query).order_by('-created_on').first()
