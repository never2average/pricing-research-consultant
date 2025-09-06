from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class TsObjectPydantic(BaseModel):
    usage_value_in_units: Optional[float] = None
    usage_unit: Optional[str] = None
    target_date: Optional[datetime] = None


class CustomerSegmentPydantic(BaseModel):
    segment_name: Optional[str] = None
    segment_cdp_uid: Optional[str] = None
    segment_description: Optional[str] = None
    segment_filter_logic: Optional[str] = None
    segment_usage_summary: Optional[str] = None
    segment_revenue_attribution_summary: Optional[str] = None


class ProductPydantic(BaseModel):
    product_name: Optional[str] = None
    product_industry: Optional[str] = None
    product_description: Optional[str] = None
    product_icp_summary: Optional[str] = None
    product_categories: Optional[List[str]] = None
    product_categories_vs_id: Optional[str] = None
    product_feature_docs: Optional[List[str]] = None
    product_feature_docs_vs_id: Optional[str] = None
    product_marketing_docs: Optional[List[str]] = None
    product_marketing_docs_vs_id: Optional[str] = None
    product_technical_docs: Optional[List[str]] = None
    product_technical_docs_vs_id: Optional[str] = None



class PricingExperimentPydantic(BaseModel):
    product: Optional[ProductPydantic] = None
    experiment_number: Optional[int] = None
    experiment_gen_stage: Optional[str] = None
    objective: Optional[str] = None
    usecase: Optional[str] = None
    relevant_segments: Optional[List[CustomerSegmentPydantic]] = None
    positioning_summary: Optional[str] = None
    usage_summary: Optional[str] = None
    roi_gaps: Optional[str] = None
    experimental_pricing_plan: Optional[str] = None
    simulation_result: Optional[str] = None
    usage_projections: Optional[List[TsObjectPydantic]] = None
    revenue_projections: Optional[List[TsObjectPydantic]] = None
    cashflow_feasibility_comments: Optional[str] = None
    cashflow_no_negative_impact_approval_given: Optional[bool] = None
    experiment_is_deployed: Optional[bool] = None
    experiment_deployed_on: Optional[datetime] = None
    experiment_feedback_summary: Optional[str] = None
