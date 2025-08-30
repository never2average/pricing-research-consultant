import instructor
from litellm import completion
from utils.openai_client import openai_client
from pydantic import BaseModel, Field, Optional, List
from datastore.models import Product, ProductPricingModel, CustomerSegment, RecommendedPricingModel

llm_client = instructor.from_litellm(completion)

class RecommendedCustomerSegmentModel(BaseModel):
    existing_customer_segment: bool
    customer_segment_uid: Optional[str] = Field(default=None)
    customer_segment_name: Optional[str] = Field(default=None)
    customer_segment_description: Optional[str] = Field(default=None)

class RecommendedPricingModelResponse(BaseModel):
    recommended_customer_segment: List[RecommendedCustomerSegmentModel]
    unit_price: float
    min_unit_count: int
    unit_calculation_logic: str
    min_unit_utilization_period: str
    

 
experimental_pricing_recommendation_prompt = """
Background:
You are an expert pricing analyst for 

Task:

"""

def agent(product_id: str, value_capture_analysis: str)
    product = Product.objects.get(id=product_id)
    new_ab_test_pricing_model = openai_client.responses.create(
        model="gpt-5",
        reasoning={"effort": "high"},
        input=[{
            "role": "system",
            "content": experimental_pricing_recommendation_prompt,
        },
        {
            "role": "user",
            "content": value_capture_analysis
        }]
    )
    
    new_ab_test_pricing_model_structured_output = llm_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": new_ab_test_pricing_model.choices[0].message.content}
        ],
        response_format=RecommendedPricingModelResponse
    )
    
    pricing_response = new_ab_test_pricing_model_structured_output
    
    # Create and save ProductPricingModel
    pricing_model = ProductPricingModel(
        unit_price=pricing_response.unit_price,
        min_unit_count=pricing_response.min_unit_count,
        unit_calculation_logic=pricing_response.unit_calculation_logic,
        min_unit_utilization_period=pricing_response.min_unit_utilization_period
    )
    pricing_model.save()
    
    customer_segment = CustomerSegment.objects.get(id=customer_segment_id)
    
    recommended_pricing = RecommendedPricingModel(
        product=product,
        customer_segment=customer_segment,
        pricing_plan=pricing_model
    )
    recommended_pricing.save()
    
    return {
        'pricing_response': pricing_response,
        'pricing_model_id': str(pricing_model.id),
        'recommended_pricing_id': str(recommended_pricing.id)
    }