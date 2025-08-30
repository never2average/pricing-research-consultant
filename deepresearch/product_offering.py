from datastore.models import Product
from utils.openai_client import openai_client
from .prompts import product_deep_research_prompt



def agent(product_id=None, usage_scope=""):
    product = Product.objects.get(id=product_id)
    input_data = product_deep_research_prompt.format(
        product_name=product.name,
        features=product.features_description_summary,
        icp_description=product.icp_description,
    )
    
    if usage_scope:
        input_data += "\n\nThe current scope of our research is:\n" + usage_scope
    
    response = openai_client.responses.create(
        model="o3-deep-research",
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
    )
    
    return response.output_text