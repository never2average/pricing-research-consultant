from datastore.models import Product
from utils.openai_client import openai_client
from .prompts import positioning_analysis_prompt


def agent(product_id=None, experimental_pricing_research=None, pricing_objective=None):
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
    
    if pricing_objective:
        input_data = f"{input_data}\n\n## Pricing Objective:\n{pricing_objective}"
    
    tools = [
        {"type": "web_search_preview"}
    ]
    
    # Add marketing vector store if available
    if hasattr(product, 'marketing_vector_store_id') and product.marketing_vector_store_id:
        tools.append({
            "type": "file_search",
            "vector_store_ids": [
                product.marketing_vector_store_id
            ]
        })
    
    response = openai_client.responses.create(
        model="o3-deep-research",
        instructions=positioning_analysis_prompt,
        input=input_data,
        tools=tools
    )
    
    return response.content[0].text
