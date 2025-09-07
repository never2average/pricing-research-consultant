import asyncio
import json
from typing import List
from datastore.types import PricingExperimentPydantic, ExperimentGenStage
from utils.openai_client import get_openai_client


async def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()
    
    system_prompt = """
You are a senior pricing strategy consultant specializing in ROI gap analysis. Analyze the current state vs potential state to identify the TOP 3 SPECIFIC revenue and pricing optimization opportunities for this customer segment.

ANALYSIS FRAMEWORK:
1. Current State Assessment - Analyze existing positioning, usage patterns, and competitive standing
2. Market Opportunity Identification - Find gaps between current value delivery and market potential  
3. Revenue Leakage Analysis - Identify where money is left on the table
4. Competitive Positioning Gaps - Areas where stronger positioning could command premium
5. Usage-Value Misalignment - Where usage patterns suggest different pricing models
6. Quantified Impact Estimates - Size the opportunities with rough impact ranges

OUTPUT FORMAT:
Provide structured JSON with these exact keys:
- current_roi_assessment: Current ROI situation and constraints
- top_3_gaps: Array of exactly 3 gap objects, each with:
  * gap_name: Short descriptive name
  * gap_description: Detailed description of the opportunity
  * estimated_impact_range: Revenue impact estimate (e.g., "$50K-$200K annually")
  * implementation_difficulty: "Low", "Medium", or "High"
  * time_to_impact: "1-3 months", "3-6 months", or "6+ months"
  * success_probability: Percentage likelihood of success
- competitive_positioning_opportunities: Areas for pricing advantage vs competitors
- segment_specific_insights: Unique characteristics of this segment affecting pricing
- risk_factors: Key risks that could impact gap realization

REQUIREMENTS:
- Focus on the TOP 3 most impactful gaps only - be ruthlessly prioritized
- Each gap must be specific, actionable, and measurable
- Include segment-specific context in gap analysis
- Provide realistic impact estimates with confidence ranges
- Consider implementation feasibility alongside impact potential
"""

    product_name = pricing_experiment.product.product_name if pricing_experiment.product else "Unknown Product"
    product_seed_context = pricing_experiment.product_seed_context or "Not available"
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

TARGET SEGMENT DETAILS:
{segment_info}

TASK:
Conduct a comprehensive ROI gap analysis specifically for the target segment above. Identify the TOP 3 most impactful revenue and pricing optimization opportunities that are:
1. Specific to this customer segment's characteristics and behavior
2. Actionable through pricing experiments
3. Measurable and time-bound
4. Realistic given implementation constraints

Focus on segment-specific insights that differentiate this analysis from generic pricing strategies.
"""

    response = await client.responses.create(
        model="gpt-5",
        instructions=system_prompt,
        input=user_prompt,
        reasoning={"effort": "high"},
        max_output_tokens=3000,
        truncation="auto"
    )

    output_text = response.output_text or ""
    
    try:
        parsed_result = json.loads(output_text)
        return parsed_result
    except json.JSONDecodeError:
        return {"roi_analysis": output_text, "parsing_error": "Could not parse structured output"}


async def invoke_orchestrator_async(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    tasks = [invoke_agent(experiment) for experiment in experiments]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            experiments[idx].roi_gaps = f"Error in ROI analysis: {str(result)}"
        else:
            if isinstance(result, dict):
                experiments[idx].roi_gaps = json.dumps(result, indent=2)
            else:
                experiments[idx].roi_gaps = str(result)
        
        experiments[idx].experiment_gen_stage = ExperimentGenStage.ROI_GAP_ANALYZER_RUN
    
    return experiments


def invoke_orchestrator(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    return asyncio.run(invoke_orchestrator_async(experiments))
