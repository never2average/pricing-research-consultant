import asyncio
import copy
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
    return response.output_text


async def invoke_orchestrator_async(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    tasks = [invoke_agent(experiment) for experiment in experiments]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    result_experiments = []

    for idx, result in enumerate(results):
        original_experiment = experiments[idx]
        
        if isinstance(result, Exception):
            # On error, create one experiment with error info
            error_experiment = copy.deepcopy(original_experiment)
            error_experiment.roi_gaps = f"Error in ROI analysis: {str(result)}"
            error_experiment.experiment_gen_stage = ExperimentGenStage.ROI_GAP_ANALYZER_RUN
            result_experiments.append(error_experiment)
        else:
            # Ensure result is a dict before processing
            if isinstance(result, dict):
                # Parse the result to extract the 3 gaps
                gaps_data = result.get("top_3_gaps", [])
                
                # Create 3 separate experiments, one for each gap
                for gap_idx, gap in enumerate(gaps_data):
                    new_experiment = copy.deepcopy(original_experiment)
                    
                    # Store the full analysis context but focus on this specific gap
                    gap_focused_result = copy.deepcopy(result)
                    gap_focused_result["focused_gap"] = gap
                    gap_focused_result["gap_priority"] = gap_idx + 1  # 1, 2, or 3
                    
                    new_experiment.roi_gaps = gap_focused_result
                    new_experiment.experiment_gen_stage = ExperimentGenStage.ROI_GAP_ANALYZER_RUN
                    result_experiments.append(new_experiment)
                
                # If we don't have any gaps, create at least one experiment
                if len(gaps_data) == 0:
                    fallback_experiment = copy.deepcopy(original_experiment)
                    fallback_experiment.roi_gaps = result
                    fallback_experiment.experiment_gen_stage = ExperimentGenStage.ROI_GAP_ANALYZER_RUN
                    result_experiments.append(fallback_experiment)
            else:
                # Handle non-dict results
                fallback_experiment = copy.deepcopy(original_experiment)
                fallback_experiment.roi_gaps = str(result)
                fallback_experiment.experiment_gen_stage = ExperimentGenStage.ROI_GAP_ANALYZER_RUN
                result_experiments.append(fallback_experiment)
    
    return result_experiments


def invoke_orchestrator(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    return asyncio.run(invoke_orchestrator_async(experiments))
