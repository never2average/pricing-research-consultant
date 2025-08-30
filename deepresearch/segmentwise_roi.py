import instructor
from litellm import completion
from utils.openai_client import openai_client
from datastore.models import Product, CustomerSegment, ProductPricingModel, CustomerUsageAnalysis
from .prompts import roi_prompt

llm_client = instructor.from_litellm(completion)

def agent(product_id, product_research):
    all_segments = CustomerSegment.objects.filter(product=product_id)
    all_usage_analysis = CustomerUsageAnalysis.objects.filter(product=product_id)

    

    input_text = f"""
## Product Research Context
{product_research}

---
## Data Hints
Segments count: {all_segments.count()}
Usage analyses count: {all_usage_analysis.count()}
"""

    thoughts = openai_client.responses.create(
        model="gpt-5",
        instruction=roi_prompt,
        input=input_text,
        reasoning={"effort": "medium"},
        temperature=0.2,
        truncation="auto"
    )

    return thoughts.output_text