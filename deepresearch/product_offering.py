from datastore.models import Product
from utils.openai_client import openai_client
from .prompts import product_deep_research_prompt



def agent(product_id=None, usage_scope=""):
    product = Product.objects.get(id=product_id)
    input_data = f"""
## Product
{product.name}

## Core Features
{product.features_description_summary}

## Ideal Customer Profile
{product.icp_description}
"""
    if usage_scope:
        input_data = f"{input_data}\n\n## Usage Scope:\n{usage_scope}"
    
    response = openai_client.responses.create(
        model="o3-deep-research",
        instructions=product_deep_research_prompt,
        input=input_data,
        tools=[
            {"type": "web_search_preview"},
            {
                "type": "file_search",
                "vector_store_ids": [
                    product.vector_store_id
                ]
            },
            {
                "type": "code_interpreter",
                "container": {"type": "auto"}
            },
        ],
        tool_choice="auto",
        truncation="auto",
        max_tool_calls=10
    )
    
    return response.output_text