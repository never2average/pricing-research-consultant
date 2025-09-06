from pydantic import BaseModel, Field
from typing import List, Optional
import json
import instructor
from litellm import completion
import os
from dotenv import load_dotenv

load_dotenv()

client = instructor.from_litellm(completion)

class Product(BaseModel):
    name: Optional[str] = Field(default=None)
    icp_description: Optional[str] = Field(default=None)
    unit_level_cogs: Optional[str] = Field(default=None)
    features_description_summary: Optional[str] = Field(default=None)
    product_documentations: Optional[List[str]] = Field(default=None)

class PricingModel(BaseModel):
    plan_name: Optional[str] = Field(default=None)
    unit_price: Optional[float] = Field(default=None)
    min_unit_count: Optional[int] = Field(default=None)
    unit_calculation_logic: Optional[str] = Field(default=None)
    min_unit_utilization_period: Optional[str] = Field(default=None)

class UsageAnalysis(BaseModel):
    customer_uid: Optional[str] = Field(default=None)
    customer_task_to_agent: Optional[str] = Field(default=None)
    predicted_customer_satisfaction_response: Optional[float] = Field(default=None)
    predicted_customer_satisfaction_response_reasoning: Optional[str] = Field(default=None)

class CustomerSegment(BaseModel):
    customer_segment_uid: Optional[str] = Field(default=None)
    customer_segment_name: Optional[str] = Field(default=None)
    customer_segment_description: Optional[str] = Field(default=None)
    pricing_model_ids: Optional[List[int]] = Field(default=None)
    number_of_active_subscriptions: Optional[int] = Field(default=None)
    number_of_active_subscriptions_forecast: Optional[int] = Field(default=None)
    usage_analyses: Optional[List[UsageAnalysis]] = Field(default=None)

class ProductData(BaseModel):
    product: Optional[Product] = Field(default=None)
    pricing_models: Optional[List[PricingModel]] = Field(default=None)
    customer_segments: Optional[List[CustomerSegment]] = Field(default=None)

response = client.chat.completions.create(
    model="gpt-5-2025-08-07",
    api_key=os.getenv("OPENAI_API_KEY"),
    messages=[
        {"role": "system", "content": "Calculate Unit price as (3*per million token input + 1* per million token output)/ 4"},
        {"role": "user", "content": f"""
Read about all the models offered by OpenAI and format them into a product/pricing/persona JSON.
The product is OpenAI API platform, and the pricing plans are the different model-level pricings.
The customer personas are the different types of developers, companies and so on who consume OpenAI APIs.

Treat batch API and regular API as different pricing plans.
"""}],
    response_model=ProductData
)

json.dump(response.model_dump(), open("product_data.json", "w"))
