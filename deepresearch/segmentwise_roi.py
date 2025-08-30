import instructor
from litellm import completion
from utils.openai_client import openai_client
from datastore.models import Product, CustomerSegment, ProductPricingModel, CustomerUsageAnalysis

llm_client = instructor.from_litellm(completion)

def agent(product_id: str):
    all_segments = CustomerSegment.objects.filter(product=product_id)
    all_usage_analysis = CustomerUsageAnalysis.objects.filter(product=product_id)
    
    # we need to structure this such that we get the output in a table style structure.