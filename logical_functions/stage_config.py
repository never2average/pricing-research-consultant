from deepresearch.segment_research_agent import invoke_orchestrator as segment_orchestrator
from deepresearch.product_research_agent import invoke_orchestrator as product_orchestrator
from deepresearch.competitor_research_agent import invoke_orchestrator as competitor_orchestrator
from deepresearch.roi_gap_analyzer import invoke_orchestrator as roi_orchestrator
from deepresearch.experimental_pricing_generator import invoke_orchestrator as pricing_orchestrator
from deepresearch.invoke_simulations_agent import invoke_orchestrator as simulation_orchestrator
from deepresearch.scenario_builder_agent import invoke_orchestrator as scenario_orchestrator
from deepresearch.cashflow_feasibility_analyzer import invoke_orchestrator as cashflow_orchestrator
from deepresearch.marketting_material_agent import invoke_orchestrator as marketing_orchestrator

def get_stage_mapping():
    return {
        "segments_loaded": {
            "orchestrator": segment_orchestrator,
            "next_stage": "positioning_usage_analysis_done",
            "request_stage": "segments_loaded"
        },
        "positioning_usage_analysis_done": {
            "orchestrator": [product_orchestrator, competitor_orchestrator],
            "next_stage": "roi_gap_analyzer_run",
            "request_stage": "positioning_usage_analysis_done"
        },
        "roi_gap_analyzer_run": {
            "orchestrator": roi_orchestrator,
            "next_stage": "experimental_plan_generated",
            "request_stage": "roi_gap_analyzer_run"
        },
        "experimental_plan_generated": {
            "orchestrator": pricing_orchestrator,
            "next_stage": "simulations_run",
            "request_stage": "experimental_plan_generated"
        },
        "simulations_run": {
            "orchestrator": simulation_orchestrator,
            "next_stage": "scenario_builder_completed",
            "request_stage": "simulations_run"
        },
        "scenario_builder_completed": {
            "orchestrator": [scenario_orchestrator, marketing_orchestrator],
            "next_stage": "cashflow_feasibility_runs_completed",
            "request_stage": "scenario_builder_completed"
        },
        "cashflow_feasibility_runs_completed": {
            "orchestrator": cashflow_orchestrator,
            "next_stage": None,
            "request_stage": "cashflow_feasibility_runs_completed"
        }
    }

def get_stage_order():
    return [
        "segments_loaded",
        "positioning_usage_analysis_done",
        "roi_gap_analyzer_run",
        "experimental_plan_generated",
        "simulations_run",
        "scenario_builder_completed",
        "cashflow_feasibility_runs_completed"
    ]
