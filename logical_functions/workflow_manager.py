from datastore.models import PricingExperimentRequest
from logical_functions.stage_config import get_stage_mapping, get_stage_order
from logical_functions.experiment_run_manager import create_initial_experiment_run, create_experiment_run, update_current_experiment_run
from logical_functions.data_converter import convert_to_pydantic

def start_experiment_workflow(experiment_request: PricingExperimentRequest):
    stage_mapping = get_stage_mapping()
    stage_order = get_stage_order()
    
    current_run = None
    
    try:
        print(f"Starting workflow for experiment {experiment_request.experiment_number}")
        
        for stage in stage_order:
            try:
                print(f"Processing stage: {stage}")
                stage_config = stage_mapping[stage]
                
                if current_run is None:
                    current_run = create_initial_experiment_run(experiment_request, stage)
                
                experiment_data = convert_to_pydantic(current_run)
                
                orchestrators = stage_config["orchestrator"]
                if not isinstance(orchestrators, list):
                    orchestrators = [orchestrators]
                
                updated_data = [experiment_data]
                for orchestrator in orchestrators:
                    if orchestrator is None:
                        continue
                    try:
                        updated_data = orchestrator(updated_data)
                        if not updated_data:
                            print(f"Warning: {orchestrator.__name__} returned empty data")
                            updated_data = [experiment_data]
                    except Exception as orchestrator_error:
                        print(f"Error in {orchestrator.__name__}: {str(orchestrator_error)}")
                        updated_data = [experiment_data]
                
                if stage == "cashflow_feasibility_runs_completed":
                    current_run = update_current_experiment_run(current_run, updated_data)
                    
                    experiment_request.experiment_gen_stage = "completed"
                    experiment_request.save()
                    
                    if updated_data and updated_data[0].cashflow_feasibility_comments:
                        current_run.cashflow_no_negative_impact_approval_given = True
                        current_run.save()
                        print(f"Cashflow approval granted for experiment {experiment_request.experiment_number}")
                    
                    print(f"Experiment {experiment_request.experiment_number} completed successfully")
                    break
                else:
                    next_stage = stage_config["next_stage"]
                    current_run = create_experiment_run(experiment_request, updated_data, next_stage)
                    
                    experiment_request.experiment_gen_stage = stage_config["request_stage"]
                    experiment_request.save()
                    
                print(f"Stage {stage} completed successfully")
                    
            except Exception as stage_error:
                print(f"Error in stage {stage} for experiment {experiment_request.experiment_number}: {str(stage_error)}")
                
                experiment_request.experiment_gen_stage = f"{stage}_failed"
                experiment_request.save()
                
                if current_run:
                    current_run.experiment_gen_stage = f"{stage}_failed"
                    current_run.save()
                    
                raise Exception(f"Workflow failed at stage {stage}: {str(stage_error)}")
                
    except Exception as e:
        print(f"Critical error in workflow for experiment {experiment_request.experiment_number}: {str(e)}")
        
        experiment_request.experiment_gen_stage = "failed"
        experiment_request.save()
        
        raise
