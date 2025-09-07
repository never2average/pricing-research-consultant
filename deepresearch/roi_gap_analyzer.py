import asyncio
import json
from typing import List
from datastore.types import PricingExperimentPydantic, ExperimentGenStage
from utils.openai_client import get_openai_client


async def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()
    
    system_prompt = """
You are a senior pricing strategy consultant specializing in ROI gap analysis. Analyze the current state vs potential state to identify specific revenue and pricing optimization opportunities.

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
- identified_gaps: Specific gaps with impact potential
- competitive_positioning_opportunities: Areas for pricing advantage vs competitors
- usage_value_misalignment: Pricing model optimization opportunities  
- quantified_impact_ranges: Estimated revenue impact ranges for top opportunities
- priority_recommendations: Top 3 actionable recommendations with rationale

ANALYSIS DEPTH:
- Be specific about dollar amounts, percentages, and timeframes where possible
- Ground recommendations in the provided context data
- Focus on actionable insights that can inform pricing experiments
- Highlight quick wins vs longer-term strategic moves
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

Target Segment: {segment_info}

TASK:
Conduct a comprehensive ROI gap analysis to identify specific opportunities for pricing optimization and revenue growth. Focus on actionable insights that can guide experimental pricing strategies.
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
