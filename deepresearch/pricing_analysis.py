from utils.openai_client import openai_client
from datastore.models import Product, CustomerSegment, ProductPricingModel, PricingPlanSegmentContribution


def agent(product_id: str):
    all_segments = CustomerSegment.objects.filter(product=product_id)
    all_pricing_plans = ProductPricingModel.objects.filter(product=product_id)
    
    # We need to get some way to merge the final output of both these DB calls into a single document add it to vector store and then run deep research on it