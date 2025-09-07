import asyncio
import json
from typing import List
from datastore.types import PricingExperimentPydantic, ExperimentGenStage, TsObjectPydantic
from utils.openai_client import get_openai_client
from datetime import datetime, timedelta


async def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()
    
    system_prompt = """
You are a pricing simulation expert. Run comprehensive simulations of pricing experiments to predict outcomes across multiple scenarios.

SIMULATION FRAMEWORK:
1. Baseline Model - Current state revenue and usage patterns
2. Experimental Scenarios - Test different pricing parameters and market conditions  
3. Sensitivity Analysis - How changes in key variables affect outcomes
4. Risk Scenarios - Downside cases and their probabilities
5. Time-series Projections - Monthly forecasts over simulation period
6. Statistical Confidence - Probability ranges for key outcomes

SIMULATION COMPONENTS:
- Customer behavior modeling (adoption, churn, expansion)
- Revenue impact projections with confidence intervals
- Usage pattern changes under new pricing
- Competitive response scenarios
- Market penetration curves
- Customer lifetime value impacts

OUTPUT FORMAT:
Provide structured JSON with these exact keys:
- simulation_scenarios: List of scenarios tested with parameters
- baseline_projections: Current state projections for comparison
- experimental_projections: Results under new pricing for each scenario
- sensitivity_analysis: Key factors that most impact outcomes  
- risk_assessment: Downside scenarios and their likelihood
- confidence_intervals: Statistical ranges for revenue/usage projections
- monthly_forecasts: Time-series data for next 12 months
- recommendation_summary: Key insights and recommended next steps

REQUIREMENTS:
- Include optimistic, realistic, and pessimistic scenarios
- Provide specific numbers with confidence ranges
- Model customer segments separately where relevant
- Account for seasonality and market trends
- Include both financial and operational impact metrics
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
Run comprehensive simulations of the proposed pricing experiment. Model multiple scenarios including optimistic, realistic, and pessimistic cases. 

Provide detailed projections for:
1. Revenue impact over 12 months
2. Usage pattern changes
3. Customer behavior responses
4. Market penetration effects
5. Competitive dynamics
6. Risk factors and mitigation needs

Include specific monthly forecasts and confidence intervals for all key metrics.
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
        
        if "monthly_forecasts" in parsed_result:
            forecasts = parsed_result["monthly_forecasts"]
            base_date = datetime.now()
            
            for i in range(12):
                target_date = base_date + timedelta(days=30 * i)
                
                if isinstance(forecasts, list) and i < len(forecasts):
                    forecast = forecasts[i]
                    if isinstance(forecast, dict):
                        if "usage" in forecast:
                            usage_projections.append(TsObjectPydantic(
                                usage_value_in_units=forecast["usage"],
                                usage_unit="projected_units",
                                target_date=target_date
                            ))
                        if "revenue" in forecast:
                            revenue_projections.append(TsObjectPydantic(
                                usage_value_in_units=forecast["revenue"],
                                usage_unit="projected_revenue_usd",
                                target_date=target_date
                            ))
        
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
