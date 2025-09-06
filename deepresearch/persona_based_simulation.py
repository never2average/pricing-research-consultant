from typing import Optional
from datastore.models import Product
from utils.openai_client import openai_client
from .prompts import persona_simulation_prompt


def agent(product_id: Optional[str] = None, experimental_pricing_research: Optional[str] = None, pricing_objective: Optional[str] = None) -> str:
    """
    Persona-based Simulation Agent
    Simulates customer personas and their response to pricing strategies
    """
    product = Product.objects.get(id=product_id)
    input_data = f"""
## Product
{product.name}

## Core Features
{product.features_description_summary}

## Ideal Customer Profile
{product.icp_description}

## Experimental Pricing Research
{experimental_pricing_research or "No experimental pricing provided"}
"""
    
    if pricing_objective:
        input_data = f"{input_data}\n\n## Pricing Objective:\n{pricing_objective}"
    
    response = openai_client.responses.create(
        model="o3-deep-research",
        instructions=persona_simulation_prompt,
        input=input_data,
        tools=[
            {"type": "web_search_preview"},
            {
                "type": "file_search",
                "vector_store_ids": [
                    "vs_cxOy9F7MqC5LnBvAdrXGdxLw"
                ]
            }
        ]
    )
    
    return response.content[0].text
