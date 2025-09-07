import asyncio
import json
from typing import List
from datastore.types import PricingExperimentPydantic, ExperimentGenStage
from utils.openai_client import get_openai_client


async def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()
    
    system_prompt = """
You are a pricing strategy expert specializing in experimental pricing design. Create data-driven pricing experiments based on ROI gap analysis.

EXPERIMENTAL DESIGN FRAMEWORK:
1. Hypothesis Formation - Clear testable hypotheses based on identified gaps
2. Pricing Model Design - Specific pricing structures aligned with usage patterns
3. Test Parameters - Define variables, controls, and success metrics
4. Risk Mitigation - Identify potential downsides and safeguards
5. Implementation Roadmap - Phased rollout approach with decision gates
6. Success Metrics - KPIs and measurement framework

PRICING EXPERIMENT TYPES:
- Value-based pricing tiers
- Usage-based pricing models  
- Bundling/unbundling strategies
- Premium feature monetization
- Geographic or segment-specific pricing
- Freemium to paid conversion optimization
- Enterprise vs SMB pricing differentiation

OUTPUT FORMAT:
Provide structured JSON with these exact keys:
- experiment_hypothesis: Clear hypothesis being tested
- pricing_model_design: Detailed pricing structure and rationale
- test_parameters: Variables, sample sizes, duration, controls
- target_segments: Who will be included in the experiment
- success_metrics: Primary and secondary KPIs for evaluation
- risk_assessment: Potential risks and mitigation strategies  
- implementation_plan: Step-by-step rollout approach
- expected_outcomes: Projected impact ranges and timeline

REQUIREMENTS:
- Be specific about pricing numbers, percentages, and timeframes
- Ensure experiments are statistically sound and ethically designed
- Focus on learnings that can scale beyond the experiment
- Include both optimistic and conservative scenarios
"""

    product_name = pricing_experiment.product.product_name if pricing_experiment.product else "Unknown Product"
    product_seed_context = pricing_experiment.product_seed_context or "Not available"
    roi_gaps = pricing_experiment.roi_gaps or "No ROI analysis available"
    segment_info = pricing_experiment.relevant_segment or "Not specified"
    objective = pricing_experiment.objective or "Not specified"
    usecase = pricing_experiment.usecase or "Not specified"

    user_prompt = f"""
CONTEXT:
Product: {product_name}
Experiment Objective: {objective}
Use Case: {usecase}

PRODUCT CONTEXT:
{product_seed_context}

Target Segment: {segment_info}

TOP 3 ROI GAPS ANALYSIS:
{roi_gaps}

TASK:
Design a comprehensive pricing experiment that addresses the TOP 3 identified ROI gaps for this specific segment. Create an experiment plan that:

1. Prioritizes the highest-impact gap from the top 3 identified
2. Tests a clear hypothesis derived from the segment-specific gap analysis  
3. Includes measurable success criteria aligned with gap impact estimates
4. Incorporates appropriate risk controls based on implementation difficulty
5. Can provide actionable insights for this customer segment

Focus your experiment design on the most promising gap while considering the implementation feasibility and time-to-impact factors provided in the analysis.
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
        return {"pricing_experiment_plan": output_text, "parsing_error": "Could not parse structured output"}


async def invoke_orchestrator_async(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    tasks = [invoke_agent(experiment) for experiment in experiments]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            experiments[idx].experimental_pricing_plan = f"Error generating pricing plan: {str(result)}"
        else:
            if isinstance(result, dict):
                experiments[idx].experimental_pricing_plan = json.dumps(result, indent=2)
            else:
                experiments[idx].experimental_pricing_plan = str(result)
        
        experiments[idx].experiment_gen_stage = ExperimentGenStage.EXPERIMENTAL_PLAN_GENERATED
    
    return experiments


def invoke_orchestrator(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    return asyncio.run(invoke_orchestrator_async(experiments))
