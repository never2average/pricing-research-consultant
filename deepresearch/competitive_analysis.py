from datastore.models import Product
from utils.openai_client import openai_client
from .prompts import competitive_analysis_prompt


def agent(product_id=None, pricing_objective=None):
    """
    Competitive Analysis Agent
    Analyzes competitive landscape and pricing strategies
    """
    product = Product.objects.get(id=product_id)
    competitor_info = ""
    if product.competitors:
        competitor_info = "\n## Known Competitors\n"
        for i, competitor in enumerate(product.competitors, 1):
            competitor_info += f"\n### Competitor {i}: {competitor.competitor_name}\n"
            if competitor.website_url:
                competitor_info += f"Website: {competitor.website_url}\n"
            if competitor.product_description:
                competitor_info += f"Product Description: {competitor.product_description}\n"
    
    input_data = f"""
## Product
{product.name}

## Core Features
{product.features_description_summary}

## Ideal Customer Profile
{product.icp_description}

## Product Category
{product.category}
{competitor_info}
"""
    
    if pricing_objective:
        input_data = f"{input_data}\n\n## Pricing Objective:\n{pricing_objective}"
    
    tools = [{"type": "web_search_preview"}]
    
    # Add file search tools for product documentation if available
    vector_stores = []
    if product.vector_store_id:
        vector_stores.append(product.vector_store_id)
    if product.marketing_vector_store_id:
        vector_stores.append(product.marketing_vector_store_id)
    
    if vector_stores:
        tools.append({
            "type": "file_search",
            "vector_store_ids": vector_stores
        })
    
    response = openai_client.responses.create(
        model="o3-deep-research",
        instructions=competitive_analysis_prompt,
        input=input_data,
        tools=tools
    )
    
    return response.content[0].text
