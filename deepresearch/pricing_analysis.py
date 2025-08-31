from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel, Field, Optional, List
from utils.openai_client import openai_client, litellm_client
from datastore.models import Product, CustomerSegment, ProductPricingModel
from datastore.models import PricingPlanSegmentContribution, TimeseriesData
from .prompts import pricing_analysis_system_prompt, structured_parsing_system_prompt


class RevenuePoint(BaseModel):
    date: str
    revenue: float

class SegmentPlanForecast(BaseModel):
    pricing_plan_id: Optional[str] = Field(default=None)
    customer_segment_uid: Optional[str] = Field(default=None)
    customer_segment_name: Optional[str] = Field(default=None)
    revenue_forecast_ts_data: Optional[List[RevenuePoint]] = Field(default=None)
    active_subscriptions_forecast: Optional[List[RevenuePoint]] = Field(default=None)

class PricingAnalysisResponse(BaseModel):
    forecasts: List[SegmentPlanForecast]

def agent(product_id: str, segment_ids: List[str]=None):
    product = Product.objects(id=ObjectId(product_id)).first()
    if segment_ids:
        all_segments = CustomerSegment.objects(
            product=ObjectId(product_id),
            id__in=segment_ids
        ).all()
    else:
        all_segments = CustomerSegment.objects(
            product=ObjectId(product_id),
        ).all()
        
    all_segment_pricing_plans = PricingPlanSegmentContribution.objects(
        product=ObjectId(product_id),
        customer_segment__in=all_segments
    ).all()

    # Build markdown table for segmentwise usage/revenue
    table_rows = ["| Segment | Plan | Current Revenue | Current Subscriptions | Forecast Revenue | Forecast Subscriptions |"]
    table_rows.append("|---------|------|-----------------|----------------------|------------------|------------------------|")

    for plan_contribution in all_segment_pricing_plans:
        segment_name = plan_contribution.customer_segment.customer_segment_name
        plan_name = plan_contribution.pricing_plan.unit_calculation_logic or f"Plan {str(plan_contribution.pricing_plan.id)}"

        # Get latest revenue and subscriptions data
        current_revenue = plan_contribution.revenue_ts_data[-1].value if plan_contribution.revenue_ts_data else 0
        current_subs = plan_contribution.active_subscriptions[-1].value if plan_contribution.active_subscriptions else 0

        # Get latest forecast data
        forecast_revenue = plan_contribution.revenue_forecast_ts_data[-1].value if plan_contribution.revenue_forecast_ts_data else 0
        forecast_subs = plan_contribution.active_subscriptions_forecast[-1].value if plan_contribution.active_subscriptions_forecast else 0

        table_rows.append(f"| {segment_name} | {plan_name} | ${current_revenue:,.0f} | {current_subs:,.0f} | ${forecast_revenue:,.0f} | {forecast_subs:,.0f} |")

    table_content = "\n".join(table_rows)

    prompt = f"""
## Product Name:
{product.name}

## Product Description:
{product.description}

## Pricing Content:
{table_content}
"""
    
    draft = openai_client.responses.create(
        model="gpt-5",
        reasoning={"effort": "low"},
        temperature=0.1,
        truncation="auto",
        tool_choice="auto",
        max_tool_calls=10,
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
            }
        ],
        input=[
            {"role": "system", "content": pricing_analysis_system_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    parsed = litellm_client.chat.completions.create(
        model="together_ai/moonshotai/Kimi-K2-Instruct",
        messages=[
            {"role": "system", "content": structured_parsing_system_prompt},
            {"role": "user", "content": draft.output_text}
        ],
        response_model=PricingAnalysisResponse,
        temperature=0.0
    )

    return draft.output_text