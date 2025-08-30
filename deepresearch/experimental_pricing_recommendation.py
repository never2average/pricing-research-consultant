import instructor
from litellm import completion
from utils.openai_client import openai_client
from pydantic import BaseModel, Field, Optional, List
from datetime import datetime
from datastore.models import Product, ProductPricingModel, CustomerSegment, RecommendedPricingModel, TimeseriesData

llm_client = instructor.from_litellm(completion)

class ForwardProjections(BaseModel):
    date: str
    revenue: float
    margin: float
    profit: float
    customer_count: int

class RecommendedCustomerSegmentModel(BaseModel):
    existing_customer_segment: bool
    customer_segment_uid: Optional[str] = Field(default=None)
    customer_segment_name: Optional[str] = Field(default=None)
    customer_segment_description: Optional[str] = Field(default=None)
    projection: List[ForwardProjections]

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

def agent(product_id: str, value_capture_analysis: str) -> RecommendedPricingModelResponse:
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
    
    pricing_response = llm_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Please parse the following text into the given schema"},
            {"role": "user", "content": new_ab_test_pricing_model.output_text}
        ],
        response_format=RecommendedPricingModelResponse
    )
    
    pricing_model = ProductPricingModel(
        unit_price=pricing_response.unit_price,
        min_unit_count=pricing_response.min_unit_count,
        unit_calculation_logic=pricing_response.unit_calculation_logic,
        min_unit_utilization_period=pricing_response.min_unit_utilization_period
    )
    pricing_model.save()
    
    created_customer_segment_ids = []
    created_recommended_pricing_ids = []
    first_recommended_pricing_id = None
    
    for seg in pricing_response.recommended_customer_segment:
        customer_segment = None
        if seg.existing_customer_segment:
            if seg.customer_segment_uid:
                customer_segment = CustomerSegment.objects(product=product, customer_segment_uid=seg.customer_segment_uid).first()
            if customer_segment is None and seg.customer_segment_name:
                customer_segment = CustomerSegment.objects(product=product, customer_segment_name=seg.customer_segment_name).first()
        
        if customer_segment is None:
            customer_segment = CustomerSegment(
                product=product,
                customer_segment_uid=seg.customer_segment_uid or None,
                customer_segment_name=seg.customer_segment_name or None,
                customer_segment_description=seg.customer_segment_description or None
            )
            customer_segment.save()
        
        created_customer_segment_ids.append(str(customer_segment.id))
        
        revenue_ts = []
        for fp in seg.projection:
            parsed_date = None
            try:
                parsed_date = datetime.fromisoformat(fp.date)
            except:
                try:
                    parsed_date = datetime.strptime(fp.date, "%Y-%m-%d")
                except:
                    try:
                        parsed_date = datetime.strptime(fp.date, "%Y-%m-%dT%H:%M:%S")
                    except:
                        parsed_date = None
            if parsed_date is not None:
                revenue_ts.append(TimeseriesData(date=parsed_date, value=fp.revenue))
        
        recommended_pricing = RecommendedPricingModel(
            product=product,
            customer_segment=customer_segment,
            pricing_plan=pricing_model,
            new_revenue_forecast_ts_data=revenue_ts
        )
        recommended_pricing.save()
        if first_recommended_pricing_id is None:
            first_recommended_pricing_id = str(recommended_pricing.id)
        created_recommended_pricing_ids.append(str(recommended_pricing.id))
    
    return {
        'pricing_response': pricing_response,
        'pricing_model_id': str(pricing_model.id),
        'customer_segment_ids': created_customer_segment_ids,
        'recommended_pricing_id': first_recommended_pricing_id,
        'recommended_pricing_ids': created_recommended_pricing_ids
    }