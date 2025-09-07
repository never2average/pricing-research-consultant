import asyncio
import json
from typing import List
from datastore.types import PricingExperimentPydantic, ExperimentGenStage, TsObjectPydantic
from utils.openai_client import get_openai_client
from datetime import datetime, timedelta


async def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()
    
    system_prompt = """
You are a pricing simulation expert. Run exactly 3 DISTINCT simulations of the pricing experiment to predict outcomes across different scenarios.

REQUIRED 3 SIMULATIONS:
1. CONSERVATIVE SCENARIO - Lower adoption, higher churn, conservative market response
2. REALISTIC SCENARIO - Most likely outcomes based on market data and trends
3. OPTIMISTIC SCENARIO - Higher adoption, lower churn, favorable market conditions

SIMULATION FRAMEWORK FOR EACH:
1. Customer Behavior Modeling - Adoption rates, churn patterns, usage expansion
2. Revenue Impact Projections - Monthly revenue changes with confidence intervals
3. Market Dynamics - Competitive responses and market penetration
4. Risk Factors - Specific risks and their probability-weighted impacts
5. Time-series Forecasts - 12-month projections for key metrics

OUTPUT FORMAT:
Provide structured JSON with these exact keys:
- simulation_summary: Overview of the 3 simulation approach
- simulation_1_conservative: Complete analysis for conservative scenario with:
  * scenario_name: "Conservative"
  * key_assumptions: List of conservative assumptions
  * monthly_forecasts: 12-month revenue/usage projections
  * risk_factors: Specific risks in this scenario
  * success_probability: Likelihood of achieving targets
- simulation_2_realistic: Complete analysis for realistic scenario with same structure
- simulation_3_optimistic: Complete analysis for optimistic scenario with same structure
- comparative_analysis: Side-by-side comparison of the 3 scenarios
- recommendation_summary: Which scenario to plan for and why

REQUIREMENTS:
- Each simulation must have distinct assumptions and parameters
- Provide specific numbers with confidence ranges for all 3
- Include 12-month monthly forecasts for each scenario
- Explain key differences between the scenarios
- Recommend which scenario to use for planning purposes
"""

    product_name = pricing_experiment.product.product_name if pricing_experiment.product else "Unknown Product"
    experimental_plan = pricing_experiment.experimental_pricing_plan or "No pricing plan available"
    objective = pricing_experiment.objective or "Not specified"
    usecase = pricing_experiment.usecase or "Not specified"
    segment_info = pricing_experiment.relevant_segment or "Not specified"

    user_prompt = f"""
CONTEXT:
Product: {product_name}
Experiment Objective: {objective}
Use Case: {usecase}
Target Segment: {segment_info}

EXPERIMENTAL PRICING PLAN:
{experimental_plan}

TASK:
Run exactly 3 DISTINCT simulations of the proposed pricing experiment:

1. CONSERVATIVE SIMULATION: Model cautious adoption, higher churn, slower growth
2. REALISTIC SIMULATION: Model most likely outcomes based on historical data  
3. OPTIMISTIC SIMULATION: Model favorable conditions, strong adoption, lower churn

For EACH simulation, provide:
- Specific assumptions and parameters
- 12-month revenue and usage projections
- Key risk factors and mitigation strategies
- Success probability and confidence intervals
- Monthly forecasts with different growth trajectories

Compare all 3 simulations and recommend which scenario to use for planning and decision-making.
"""

    response = await client.responses.create(
        model="gpt-5",
        instructions=system_prompt,
        input=user_prompt,
        reasoning={"effort": "high"},
        max_output_tokens=4000,
        truncation="auto"
    )

    output_text = response.output_text or ""
    
    try:
        parsed_result = json.loads(output_text)
        
        usage_projections = []
        revenue_projections = []
        base_date = datetime.now()
        
        # Extract projections from all 3 simulations (prioritize realistic scenario)
        simulation_keys = ["simulation_2_realistic", "simulation_1_conservative", "simulation_3_optimistic"]
        
        for sim_key in simulation_keys:
            if sim_key in parsed_result:
                sim_data = parsed_result[sim_key]
                if "monthly_forecasts" in sim_data:
                    forecasts = sim_data["monthly_forecasts"]
                    
                    # Use realistic scenario for main projections, but store all 3
                    if sim_key == "simulation_2_realistic":
                        for i in range(12):
                            target_date = base_date + timedelta(days=30 * i)
                            
                            if isinstance(forecasts, list) and i < len(forecasts):
                                forecast = forecasts[i]
                                if isinstance(forecast, dict):
                                    if "usage" in forecast:
                                        usage_projections.append(TsObjectPydantic(
                                            usage_value_in_units=forecast["usage"],
                                            usage_unit="realistic_scenario_units",
                                            target_date=target_date
                                        ))
                                    if "revenue" in forecast:
                                        revenue_projections.append(TsObjectPydantic(
                                            usage_value_in_units=forecast["revenue"],
                                            usage_unit="realistic_scenario_revenue_usd",
                                            target_date=target_date
                                        ))
                break
        
        return {
            "simulation_result": parsed_result,
            "usage_projections": usage_projections,
            "revenue_projections": revenue_projections
        }
        
    except json.JSONDecodeError:
        return {"simulation_result": output_text, "parsing_error": "Could not parse structured output"}


async def invoke_orchestrator_async(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    tasks = [invoke_agent(experiment) for experiment in experiments]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            experiments[idx].simulation_result = f"Error running simulations: {str(result)}"
        else:
            if isinstance(result, dict):
                experiments[idx].simulation_result = json.dumps(result.get("simulation_result", result), indent=2)
                experiments[idx].usage_projections = result.get("usage_projections", [])
                experiments[idx].revenue_projections = result.get("revenue_projections", [])
            else:
                experiments[idx].simulation_result = str(result)
        
        experiments[idx].experiment_gen_stage = ExperimentGenStage.SIMULATIONS_RUN
    
    return experiments


def invoke_orchestrator(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    return asyncio.run(invoke_orchestrator_async(experiments))
