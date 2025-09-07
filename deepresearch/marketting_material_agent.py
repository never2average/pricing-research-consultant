# pyright: reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportMissingParameterType=false, reportReturnType=false
# ruff: noqa: ANN,ANN001,ANN201
# noqa: ANN
import asyncio
import json
from typing import List
from utils.openai_client import get_openai_client
from datastore.types import PricingExperimentPydantic


def _build_vector_store_ids(pricing_experiment: PricingExperimentPydantic):
    ids = []
    if pricing_experiment and pricing_experiment.product:
        ids.extend([
            pricing_experiment.product.product_marketing_docs_vs_id,
            pricing_experiment.product.product_feature_docs_vs_id,
            pricing_experiment.product.product_categories_vs_id,
            pricing_experiment.product.product_usage_docs_vs_id,
            pricing_experiment.product.product_technical_docs_vs_id,
        ])
        competitor = getattr(pricing_experiment.product, "product_competitors", None)
        if competitor and getattr(competitor, "competitor_vs_id", None):
            ids.append(competitor.competitor_vs_id)
    return [i for i in ids if i]


async def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()

    instructions = """
You are a senior B2B positioning strategist. Use only provided sources. Produce:
- positioning_summary: Clear POV on differentiation vs competitors, ICP resonance, category narrative.
- usage_summary: How target users actually use the product today; top workflows; language customers use.

Rules:
- Ground every claim in the provided sources. If missing, state it explicitly.
- Prefer marketing materials for narrative; prefer technical/usage docs for workflows.
- If competitor info is present, contrast explicitly and fairly.
- Be concise and decision-oriented.
"""

    product_name = pricing_experiment.product.product_name if pricing_experiment.product else "Unknown"
    seed = pricing_experiment.product_seed_context or ""
    objective = pricing_experiment.objective or ""
    usecase = pricing_experiment.usecase or ""

    user_input = f"""
Context
- Product: {product_name}
- Objective: {objective}
- Use Case: {usecase}
- Product Seed Context (verbatim, prioritize where conflicts arise):\n{seed}

Output JSON exactly with keys: positioning_summary, usage_summary
"""

    vector_store_ids = _build_vector_store_ids(pricing_experiment)

    response = await client.responses.create(
        model="gpt-5",
        instructions=instructions,
        input=user_input,
        tools=[
            {"type": "file_search", "vector_store_ids": vector_store_ids},
            {"type": "web_search_preview"},
        ],
        tool_choice="auto",
        max_tool_calls=10,
        reasoning={"effort": "high"},
        max_output_tokens=2000,
        truncation="auto"
    )

    output_text = response.output_text or ""
    positioning_summary = None
    usage_summary = None
    try:
        data = json.loads(output_text)
        positioning_summary = data.get("positioning_summary")
        usage_summary = data.get("usage_summary")
    except Exception:
        positioning_summary = output_text.strip() if output_text else None
        usage_summary = None

    return {
        "positioning_summary": positioning_summary,
        "usage_summary": usage_summary,
    }


async def invoke_orchestrator_async(experiments: List[PricingExperimentPydantic]):
    tasks = [invoke_agent(experiment) for experiment in experiments]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            experiments[idx].positioning_summary = None
            experiments[idx].usage_summary = None
        else:
            experiments[idx].positioning_summary = result.get("positioning_summary")
            experiments[idx].usage_summary = result.get("usage_summary")
        experiments[idx].experiment_gen_stage = "positioning_usage_analysis_done"
    return experiments


def invoke_orchestrator(experiments: List[PricingExperimentPydantic]):
    return asyncio.run(invoke_orchestrator_async(experiments))
