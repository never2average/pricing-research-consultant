from datastore.models import Product
from utils.openai_client import openai_client
from .prompts import positioning_analysis_prompt


def agent(product_id=None, experimental_pricing_research=None):
    """
    Positioning Analysis Agent
    Analyzes market positioning and pricing strategy alignment
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
    
    response = openai_client.responses.create(
        model="o3-deep-research",
        instructions=positioning_analysis_prompt,
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
