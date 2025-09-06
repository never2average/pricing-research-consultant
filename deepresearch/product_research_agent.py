import asyncio
from typing import List
from datastore.types import PricingExperimentPydantic
from utils.openai_client import get_openai_client

async def invoke_agent(pricing_experiment: PricingExperimentPydantic):
    client = get_openai_client()
    response = await client.responses.create(
        model="gpt-5",
        instructions="""
<role>
    You are an expert product analyst. Only use the provided docs.
</role>

<objective>
    Produce a concise, decision-grade summary of the product for the requested audience.
</objective>

<scope>
    - Normalize multiple doc types (guides, API refs, release notes, pricing, FAQs, tickets, blogs).
    - Prefer newer info when conflicts occur; call out disagreements explicitly.
</scope>

<extraction>
    Return these facts: purpose, target users, value prop, core features, architecture, integrations, pricing/licensing, setup/requirements, security/compliance, performance/SLOs, limitations/known issues, roadmap hints & recent changes (6–12 months), ideal customers/use cases. Flag any missing/ambiguous info.
</extraction>

<grounding>
    Do not add facts not present in docs. After each section, include bracketed source ids like [1], [2] that map to a Sources list (title, date, URL).
    If a claim lacks support, label it “uncorroborated”.
</grounding>

<format>
    If output_mode=markdown, produce sections in this exact order:
    Overview (1 paragraph)
    Key Capabilities (bullets)
    How It Works (short)
    Integrations & Dependencies
    Setup & Requirements
    Security & Compliance
    Pricing/Licensing (if available)
    Limitations & Known Issues
    Ideal Customers & Use Cases
    Recent Changes (last 6–12 months)
    Open Questions / Gaps
    Sources (numbered, title/date/link)

    If output_mode=json, conform exactly to the schema provided by the caller.
</format>

<audience_tuning>
    Match tone and depth to audience and depth.
    - executive ≈ 300–500 words
    - practitioner ≈ 800–1200 words with specifics.
    If over limit, keep highest-impact facts for the audience.
</audience_tuning>

<dates>Convert relative dates to absolute calendar dates when possible.</dates>
""",
        input="""
Summarize the product below from its documentation.

Instructions
    - Use only the provided docs; prefer newer info.
    - Cite with bracketed ids [id] after each section and list full “Sources” at the end.
    - If pricing or security details are missing, state that explicitly.
    - If docs are long, chunk and synthesize—stay within the depth limit.

Deliverable
    - A grounded, de-duplicated product summary that satisfies the System <format>.
    - End with an overall confidence (high/medium/low) and why.
""",
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [
                    pricing_experiment.product.product_categories_vs_id,
                    pricing_experiment.product.product_feature_docs_vs_id,
                    pricing_experiment.product.product_technical_docs_vs_id,
                ]
            },
            {"type": "web_search_preview"},
        ],
        max_output_tokens=4000,
        tool_choice="auto",
        max_tool_calls=10,
        reasoning={"effort": "medium"}
    )
    return response.output_text


async def invoke_orchestrator_async(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    tasks = [invoke_agent(experiment) for experiment in experiments]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            experiments[idx].product_seed_context = None
        else:
            experiments[idx].product_seed_context = result
        experiments[idx].experiment_gen_stage = "product_context_initialized"
    return experiments


def invoke_orchestrator(experiments: List[PricingExperimentPydantic]) -> List[PricingExperimentPydantic]:
    return asyncio.run(invoke_orchestrator_async(experiments))
