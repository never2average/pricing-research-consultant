from datastore.models import Product
from utils.openai_client import openai_client
from .prompts import competitive_analysis_prompt


def agent(product_id=None, pricing_objective=None):
    """
    Competitive Analysis Agent
    Analyzes competitive landscape and pricing strategies
    """
    product = Product.objects.get(id=product_id)
    input_data = f"""
## Product
{product.name}

## Core Features
{product.features_description_summary}

## Ideal Customer Profile
{product.icp_description}

## Product Category
{product.category}
"""
    
    if pricing_objective:
        input_data = f"{input_data}\n\n## Pricing Objective:\n{pricing_objective}"
    
    response = openai_client.responses.create(
        model="o3-deep-research",
        instructions=competitive_analysis_prompt,
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
