from datastore.models import Product
from utils.openai_client import openai_client
from .prompts import longterm_revenue_prompt


def agent(product_id=None, segment_research=None, pricing_research=None, product_research=None, pricing_objective=None):
    """
    Long-term Revenue Potential Agent
    Analyzes customer lifetime value and long-term revenue potential
    """
    product = Product.objects.get(id=product_id)
    input_data = f"""
## Product
{product.name}

## Core Features
{product.features_description_summary}

## Ideal Customer Profile
{product.icp_description}

## Product Research Context
{product_research or "No product research provided"}

## Segment Research Context
{segment_research or "No segment research provided"}

## Pricing Research Context
{pricing_research or "No pricing research provided"}
"""
    
    if pricing_objective:
        input_data = f"{input_data}\n\n## Pricing Objective:\n{pricing_objective}"
    
    response = openai_client.responses.create(
        model="o3-deep-research",
        instructions=longterm_revenue_prompt,
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
