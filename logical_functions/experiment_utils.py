from deepresearch.experiment_feedback_summarizer import invoke_orchestrator as feedback_orchestrator
from datastore.models import PricingExperimentRequest, PricingExperimentRuns
from logical_functions.data_converter import convert_to_pydantic
from logical_functions.experiment_run_manager import create_experiment_run

def update_experiment_feedback_data(experiment_request: PricingExperimentRequest):
    try:
        latest_run = PricingExperimentRuns.objects(experiment_request=experiment_request).order_by('-created_on').first()
        if not latest_run:
            raise Exception("No experiment runs found for this request")
        
        experiment_data = convert_to_pydantic(latest_run)
        feedback_data = feedback_orchestrator([experiment_data])
        
        feedback_run = create_experiment_run(experiment_request, feedback_data, "feedback_collected")
        print(f"Experiment {experiment_request.experiment_number} feedback collected and saved")
        return feedback_run
        
    except Exception as e:
        print(f"Error collecting feedback for experiment {experiment_request.experiment_number}: {str(e)}")
        raise

def get_completed_experiments_for_deployment():
    completed_runs = PricingExperimentRuns.objects(
        cashflow_no_negative_impact_approval_given=True,
        experiment_is_deployed=False,
        experiment_gen_stage="completed"
    )
    return [run.experiment_request for run in completed_runs]
