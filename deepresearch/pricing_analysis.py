import instructor
from litellm import completion
from utils.openai_client import openai_client
from pydantic import BaseModel, Field, Optional, List
from datetime import datetime
from datastore.models import Product, CustomerSegment, ProductPricingModel, PricingPlanSegmentContribution, TimeseriesData
from .prompts import pricing_analysis_system_prompt, pricing_analysis_parse_prompt


llm_client = instructor.from_litellm(completion)

class RevenuePoint(BaseModel):
    date: str
    revenue: float

class SegmentPlanForecast(BaseModel):
    customer_segment_uid: Optional[str] = Field(default=None)
    customer_segment_name: Optional[str] = Field(default=None)
    pricing_plan_id: Optional[str] = Field(default=None)
    number_of_active_subscriptions: Optional[int] = Field(default=None)
    number_of_active_subscriptions_forecast: Optional[int] = Field(default=None)
    revenue_ts_data: List[RevenuePoint] = []
    revenue_forecast_ts_data: List[RevenuePoint] = []

class PricingAnalysisResponse(BaseModel):
    forecasts: List[SegmentPlanForecast]

def agent(product_id: str):
    product = Product.objects.get(id=product_id)
    all_segments = CustomerSegment.objects.filter(product=product)
    all_pricing_plans = ProductPricingModel.objects.all()
    
    context_segments = []
    for s in all_segments:
        context_segments.append({
            "id": str(s.id),
            "uid": s.customer_segment_uid,
            "name": s.customer_segment_name,
            "description": s.customer_segment_description
        })
    
    context_plans = []
    for p in all_pricing_plans:
        context_plans.append({
            "id": str(p.id),
            "unit_price": p.unit_price,
            "min_unit_count": p.min_unit_count,
            "unit_calculation_logic": p.unit_calculation_logic,
            "min_unit_utilization_period": p.min_unit_utilization_period
        })
    
    prompt = f"""
You are a pricing analyst. Given segments and pricing plans for product '{product.name}', output structured forecasts per segment-plan.

Segments:\n{context_segments}\n\nPlans:\n{context_plans}

Return only fields required by the schema.
"""
    
    draft = openai_client.responses.create(
        model="gpt-5",
        reasoning={"effort": "high"},
        input=[
            {"role": "system", "content": pricing_analysis_system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    
    parsed = llm_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": pricing_analysis_parse_prompt},
            {"role": "user", "content": draft.output_text}
        ],
        response_format=PricingAnalysisResponse
    )
    
    created_ids = []
    for f in parsed.forecasts:
        seg = None
        if f.customer_segment_uid:
            seg = CustomerSegment.objects(product=product, customer_segment_uid=f.customer_segment_uid).first()
        if seg is None and f.customer_segment_name:
            seg = CustomerSegment.objects(product=product, customer_segment_name=f.customer_segment_name).first()
        if seg is None:
            continue
        
        plan = None
        if f.pricing_plan_id:
            try:
                plan = ProductPricingModel.objects.get(id=f.pricing_plan_id)
            except:
                plan = None
        if plan is None:
            continue
        
        revenue_ts = []
        for rp in f.revenue_ts_data:
            dt = None
            try:
                dt = datetime.fromisoformat(rp.date)
            except:
                try:
                    dt = datetime.strptime(rp.date, "%Y-%m-%d")
                except:
                    try:
                        dt = datetime.strptime(rp.date, "%Y-%m-%dT%H:%M:%S")
                    except:
                        dt = None
            if dt is not None:
                revenue_ts.append(TimeseriesData(date=dt, value=rp.revenue))
        
        revenue_forecast_ts = []
        for rp in f.revenue_forecast_ts_data:
            dt = None
            try:
                dt = datetime.fromisoformat(rp.date)
            except:
                try:
                    dt = datetime.strptime(rp.date, "%Y-%m-%d")
                except:
                    try:
                        dt = datetime.strptime(rp.date, "%Y-%m-%dT%H:%M:%S")
                    except:
                        dt = None
            if dt is not None:
                revenue_forecast_ts.append(TimeseriesData(date=dt, value=rp.revenue))
        
        doc = PricingPlanSegmentContribution(
            product=product,
            customer_segment=seg,
            pricing_plan=plan,
            number_of_active_subscriptions=f.number_of_active_subscriptions or 0,
            number_of_active_subscriptions_forecast=f.number_of_active_subscriptions_forecast or 0,
            revenue_ts_data=revenue_ts,
            revenue_forecast_ts_data=revenue_forecast_ts
        )
        doc.save()
        created_ids.append(str(doc.id))
    
    return {
        'pricing_analysis_response': parsed,
        'created_contribution_ids': created_ids
    }