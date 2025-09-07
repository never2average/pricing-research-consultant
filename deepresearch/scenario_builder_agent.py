import asyncio
import json
from typing import List
from datastore.types import PricingExperimentPydantic, ExperimentGenStage
from utils.openai_client import get_openai_client


async def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()
    
    system_prompt = """
You are a scenario planning expert specializing in pricing strategy. Create comprehensive scenarios to test pricing experiments under different market conditions.

SCENARIO BUILDING FRAMEWORK:
1. Market Environment Scenarios - Bull, bear, and neutral market conditions
2. Competitive Response Scenarios - How competitors might react
3. Customer Behavior Scenarios - Different adoption and churn patterns  
4. Economic Scenarios - Varying budget constraints and spending patterns
5. Operational Scenarios - Internal capacity and resource constraints
6. Technology Scenarios - Platform changes and feature evolution

SCENARIO DIMENSIONS:
- Market demand levels (high/medium/low growth)
- Competitive intensity (aggressive/moderate/passive responses)  
- Customer price sensitivity (elastic/inelastic demand)
- Economic environment (recession/stable/growth)
- Internal execution capability (optimal/realistic/constrained)
- Technology adoption rates (fast/medium/slow)

OUTPUT FORMAT:
Provide structured JSON with these exact keys:
- scenario_matrix: Grid of scenarios with key parameters
- baseline_scenario: Most likely/expected scenario details
- optimistic_scenario: Best case scenario and required conditions
- pessimistic_scenario: Worst case scenario and risk factors
- black_swan_scenarios: Low probability, high impact events
- scenario_probabilities: Estimated likelihood of each scenario
- key_assumptions: Critical assumptions underlying each scenario
- monitoring_indicators: Early warning signals to track
- contingency_plans: Response strategies for each scenario type

REQUIREMENTS:
- Be specific about market conditions, competitive moves, and customer responses
- Include quantitative parameters where possible (growth rates, price changes, etc.)
- Consider both internal and external factors
- Account for interdependencies between scenario dimensions
- Provide actionable insights for each scenario
"""

    product_name = pricing_experiment.product.product_name if pricing_experiment.product else "Unknown Product"
    experimental_plan = pricing_experiment.experimental_pricing_plan or "No pricing plan available"
    simulation_result = pricing_experiment.simulation_result or "No simulation data available"
    objective = pricing_experiment.objective or "Not specified"
    usecase = pricing_experiment.usecase or "Not specified"

    user_prompt = f"""
CONTEXT:
Product: {product_name}
Experiment Objective: {objective}
Use Case: {usecase}

EXPERIMENTAL PRICING PLAN:
{experimental_plan}

SIMULATION RESULTS:
{simulation_result}

TASK:
Build comprehensive scenarios for testing the pricing experiment under different market conditions. Create a scenario matrix that covers the key uncertainties and their potential impacts.

Focus on scenarios that:
1. Test the robustness of the pricing strategy
2. Identify critical success factors and failure modes
3. Provide early warning indicators to monitor
4. Suggest contingency plans for different outcomes
5. Help prioritize which scenarios to prepare for

Include specific market conditions, competitive responses, customer behaviors, and internal factors that could affect the experiment's success.
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
        return parsed_result
    except json.JSONDecodeError:
        return {"scenario_analysis": output_text, "parsing_error": "Could not parse structured output"}


async def invoke_orchestrator_async(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    tasks = [invoke_agent(experiment) for experiment in experiments]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            pass
        else:
            pass
        
        experiments[idx].experiment_gen_stage = ExperimentGenStage.SCENARIO_BUILDER_COMPLETED
    
    return experiments


def invoke_orchestrator(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    return asyncio.run(invoke_orchestrator_async(experiments))
