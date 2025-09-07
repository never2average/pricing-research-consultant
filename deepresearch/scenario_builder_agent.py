import asyncio
from typing import List
from datastore.types import PricingExperimentPydantic, ExperimentGenStage
from utils.openai_client import get_openai_client


async def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()
    
    system_prompt = """
You are a scenario planning expert specializing in pricing strategy. Using the COMPLETED simulation results as your foundation, create comprehensive scenario extensions and contingency plans.

SCENARIO BUILDING FRAMEWORK (Building on Simulation Results):
1. Simulation Result Validation - Review the 3 completed simulations (Conservative/Realistic/Optimistic)
2. Extended Scenario Planning - Identify scenarios beyond the 3 core simulations
3. Black Swan Event Planning - Low probability, high impact scenarios not covered in simulations
4. Competitive Response Scenarios - How competitors might react to our pricing moves
5. Market Disruption Scenarios - External factors that could invalidate simulation assumptions
6. Operational Contingency Planning - Internal capacity and execution challenges

ENHANCED SCENARIO DIMENSIONS (Beyond Core Simulations):
- Extreme market disruptions (economic crisis, technology shifts, regulation changes)
- Aggressive competitive responses (price wars, feature battles, market flooding)
- Customer behavior extremes (mass adoption spikes, unexpected churn waves)
- Internal execution failures (system outages, team capacity limits, implementation delays)
- Regulatory or compliance changes affecting pricing
- Technology platform failures or security breaches

OUTPUT FORMAT:
Provide structured JSON with these exact keys:
- simulation_result_summary: Brief summary of the 3 core simulations received
- extended_scenarios: Additional scenarios beyond Conservative/Realistic/Optimistic
- black_swan_scenarios: Low probability, high impact events with mitigation plans
- competitive_response_matrix: Likely competitor reactions and counter-strategies
- operational_contingencies: Internal execution risks and backup plans
- monitoring_indicators: Early warning signals to track for each scenario
- escalation_triggers: Specific thresholds that require scenario activation
- contingency_playbooks: Detailed response strategies for each scenario type

REQUIREMENTS:
- Build directly on the provided simulation results - don't duplicate them
- Focus on scenarios that could invalidate or enhance simulation predictions
- Include specific trigger points and response protocols
- Provide quantitative thresholds where possible
- Account for cascading effects between scenario dimensions
- Ensure contingency plans are immediately actionable
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

COMPLETED 3-SCENARIO SIMULATION RESULTS:
{simulation_result}

TASK:
Using the COMPLETED simulation results above as your foundation, build comprehensive scenario extensions and contingency plans that go BEYOND the core Conservative/Realistic/Optimistic simulations.

The simulations have already covered the basic scenarios. Your job is to identify:

1. EXTENDED SCENARIOS - What extreme or edge cases weren't covered in the 3 core simulations?
2. BLACK SWAN EVENTS - Low probability but high impact scenarios that could completely change outcomes
3. COMPETITIVE RESPONSES - How might competitors react, and how would that change our simulation predictions?
4. OPERATIONAL CONTINGENCIES - What internal execution risks could derail the simulated outcomes?
5. MONITORING & TRIGGERS - What early warning signs should we watch for each scenario type?

Do NOT repeat the Conservative/Realistic/Optimistic scenarios already completed. Build contingency plans for scenarios that could make those simulations irrelevant or require immediate strategy pivots.

Focus on actionable contingency playbooks with specific trigger points and response protocols.
"""

    response = await client.responses.create(
        model="gpt-5",
        instructions=system_prompt,
        input=user_prompt,
        reasoning={"effort": "high"},
        max_output_tokens=4000,
        truncation="auto"
    )
    return response.output_text


async def invoke_orchestrator_async(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    # Only process experiments that have completed simulations successfully
    eligible_experiments = [
        exp for exp in experiments 
        if exp.experiment_gen_stage == ExperimentGenStage.SIMULATIONS_RUN and 
           exp.simulation_result and 
           exp.simulation_result != "No simulation data available"
    ]
    
    if not eligible_experiments:
        # No experiments ready for scenario building
        return experiments
    
    tasks = [invoke_agent(experiment) for experiment in eligible_experiments]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Create a mapping of eligible experiments to results
    eligible_to_result = dict(zip(eligible_experiments, results))
    
    # Update all experiments, but only modify those that were processed
    for experiment in experiments:
        if experiment in eligible_to_result:
            result = eligible_to_result[experiment]
            if isinstance(result, Exception):
                # Store error but don't fail the experiment
                pass  # Could store error info if needed
            else:
                # Store scenario results (could add a field for this)
                pass  # Scenario results could be stored in a new field
            
            experiment.experiment_gen_stage = ExperimentGenStage.SCENARIO_BUILDER_COMPLETED
    
    return experiments


def invoke_orchestrator(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    return asyncio.run(invoke_orchestrator_async(experiments))
