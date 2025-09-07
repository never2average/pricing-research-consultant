import asyncio
import json
from typing import List
from datastore.types import PricingExperimentPydantic, ExperimentGenStage
from utils.openai_client import get_openai_client


def _build_vector_store_ids(pricing_experiment: PricingExperimentPydantic):
    ids = []
    if pricing_experiment and pricing_experiment.product:
        competitor = getattr(pricing_experiment.product, "product_competitors", None)
        if competitor and getattr(competitor, "competitor_vs_id", None):
            ids.append(competitor.competitor_vs_id)
        
        ids.extend([
            pricing_experiment.product.product_marketing_docs_vs_id,
            pricing_experiment.product.product_feature_docs_vs_id,
            pricing_experiment.product.product_technical_docs_vs_id,
        ])
    return [i for i in ids if i]


async def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()
    
    system_prompt = """
You are a competitive intelligence analyst specializing in pricing strategy. Conduct comprehensive competitor benchmarking to inform pricing decisions.

COMPETITIVE ANALYSIS FRAMEWORK:
1. Competitor Identification - Key players in the market space
2. Pricing Model Analysis - How competitors structure their pricing
3. Feature Comparison - What customers get at different price points
4. Market Positioning - How competitors position their value propositions
5. Pricing Strategy Assessment - Competitive pricing patterns and trends
6. Competitive Gaps - Opportunities for differentiated positioning
7. Threat Assessment - Competitive risks and defensive strategies

BENCHMARKING DIMENSIONS:
- Pricing models (subscription, usage-based, tiered, freemium, etc.)
- Price points and packaging across customer segments
- Feature differentiation and value propositions
- Go-to-market strategies and positioning messages
- Customer acquisition and retention approaches
- Recent pricing changes and market responses

OUTPUT FORMAT:
Provide structured JSON with these exact keys:
- competitor_landscape: Overview of key competitors and market dynamics
- pricing_model_analysis: How competitors structure their pricing
- price_point_benchmarks: Specific pricing data and ranges
- feature_value_comparison: Feature sets vs pricing across competitors
- positioning_differentiation: How competitors differentiate their offerings
- competitive_gaps: Opportunities for unique positioning or pricing
- threat_assessment: Competitive risks and response scenarios
- strategic_recommendations: How to compete effectively on pricing

REQUIREMENTS:
- Focus on actionable competitive intelligence
- Include specific pricing data where available
- Identify both threats and opportunities
- Consider customer perspective on competitive alternatives
- Provide strategic recommendations for competitive response
"""

    product_name = pricing_experiment.product.product_name if pricing_experiment.product else "Unknown Product"
    product_description = pricing_experiment.product.product_description if pricing_experiment.product else "Not available"
    product_seed_context = pricing_experiment.product_seed_context or "Not available"
    objective = pricing_experiment.objective or "Not specified"
    usecase = pricing_experiment.usecase or "Not specified"

    user_prompt = f"""
ANALYSIS CONTEXT:
Product: {product_name}
Product Description: {product_description}
Experiment Objective: {objective}
Use Case: {usecase}

PRODUCT CONTEXT:
{product_seed_context}

TASK:
Conduct comprehensive competitive benchmarking analysis focused on pricing strategy. Analyze how competitors price similar solutions and identify opportunities for competitive advantage.

Focus on:
1. Competitor pricing models and strategies in this space
2. Price points and packaging approaches
3. Feature differentiation and value positioning
4. Market gaps and competitive opportunities  
5. Pricing risks and defensive strategies
6. Strategic recommendations for competitive positioning

Use the provided competitor research data and market intelligence to inform your analysis.
"""

    vector_store_ids = _build_vector_store_ids(pricing_experiment)

    response = await client.responses.create(
        model="gpt-5",
        instructions=system_prompt,
        input=user_prompt,
        tools=[
            {"type": "file_search", "vector_store_ids": vector_store_ids},
            {"type": "web_search_preview"},
        ],
        tool_choice="auto",
        max_tool_calls=10,
        reasoning={"effort": "high"},
        max_output_tokens=4000,
        truncation="auto"
    )

    output_text = response.output_text or ""
    
    try:
        parsed_result = json.loads(output_text)
        return parsed_result
    except json.JSONDecodeError:
        return {"competitive_analysis": output_text, "parsing_error": "Could not parse structured output"}


async def invoke_orchestrator_async(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    tasks = [invoke_agent(experiment) for experiment in experiments]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            pass
        else:
            pass
        
        if experiments[idx].experiment_gen_stage in [ExperimentGenStage.SEGMENTS_LOADED, ExperimentGenStage.PRODUCT_CONTEXT_INITIALIZED]:
            experiments[idx].experiment_gen_stage = ExperimentGenStage.POSITIONING_USAGE_ANALYSIS_DONE
    
    return experiments


def invoke_orchestrator(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    return asyncio.run(invoke_orchestrator_async(experiments))
