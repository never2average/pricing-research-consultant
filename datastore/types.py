from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class CustomerSegmentResponse(BaseModel):
    _id: Optional[str] = None
    product: Optional[str] = None
    customer_segment_uid: str
    customer_segment_name: str
    customer_segment_description: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CompetitorResponse(BaseModel):
    competitor_name: str
    website_url: str
    product_description: str


class ProductResponse(BaseModel):
    _id: Optional[str] = None
    name: str
    icp_description: Optional[str] = None
    unit_level_cogs: Optional[str] = None
    features_description_summary: Optional[str] = None
    competitors: Optional[List[CompetitorResponse]] = None
    product_documentations: Optional[List[str]] = None
    vector_store_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


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

class CompetitorsPydantic(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    background_research_docs: Optional[List[str]] = None
    competitor_vs_id: Optional[str] = None

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
    product_usage_docs: Optional[List[str]] = None
    product_usage_docs_vs_id: Optional[str] = None
    product_competitors: Optional[CompetitorsPydantic] = None


class MonthlyProjection(BaseModel):
    month: str
    conservative_estimate: Optional[float] = None
    realistic_estimate: Optional[float] = None
    optimistic_estimate: Optional[float] = None
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None


class BreakEvenAnalysis(BaseModel):
    conservative_break_even_months: Optional[int] = None
    realistic_break_even_months: Optional[int] = None
    optimistic_break_even_months: Optional[int] = None
    customer_acquisition_required: Optional[int] = None
    break_even_conditions: Optional[str] = None


class InvestmentRequirements(BaseModel):
    upfront_investment: Optional[float] = None
    ongoing_monthly_costs: Optional[float] = None
    infrastructure_costs: Optional[float] = None
    personnel_costs: Optional[float] = None
    system_costs: Optional[float] = None
    total_investment_12_months: Optional[float] = None


class RiskAssessment(BaseModel):
    high_risk_factors: Optional[List[str]] = None
    medium_risk_factors: Optional[List[str]] = None
    low_risk_factors: Optional[List[str]] = None
    financial_risk_amount: Optional[float] = None
    risk_mitigation_strategies: Optional[List[str]] = None


class SensitivityAnalysis(BaseModel):
    key_variables: Optional[List[str]] = None
    customer_acquisition_impact: Optional[str] = None
    pricing_sensitivity: Optional[str] = None
    market_response_impact: Optional[str] = None


class FinancingNeeds(BaseModel):
    external_financing_required: Optional[bool] = None
    financing_amount: Optional[float] = None
    financing_timeline: Optional[str] = None
    recommended_financing_type: Optional[str] = None


class CashflowAnalysisResult(BaseModel):
    cash_flow_summary: Optional[str] = None
    monthly_projections: Optional[List[MonthlyProjection]] = None
    break_even_analysis: Optional[BreakEvenAnalysis] = None
    investment_requirements: Optional[InvestmentRequirements] = None
    risk_assessment: Optional[RiskAssessment] = None
    sensitivity_analysis: Optional[SensitivityAnalysis] = None
    financing_needs: Optional[FinancingNeeds] = None
    approval_recommendation: Optional[str] = None
    key_assumptions: Optional[List[str]] = None



class ExperimentGenStage(Enum):
    PRODUCT_CONTEXT_INITIALIZED = "product_context_initialized"
    SEGMENTS_LOADED = "segments_loaded"
    POSITIONING_USAGE_ANALYSIS_DONE = "positioning_usage_analysis_done"
    ROI_GAP_ANALYZER_RUN = "roi_gap_analyzer_run"
    EXPERIMENTAL_PLAN_GENERATED = "experimental_plan_generated"
    SIMULATIONS_RUN = "simulations_run"
    SCENARIO_BUILDER_COMPLETED = "scenario_builder_completed"
    CASHFLOW_FEASIBILITY_RUNS_COMPLETED = "cashflow_feasibility_runs_completed"
    COMPLETED = "completed"
    DEPLOYED = "deployed"
    FEEDBACK_COLLECTED = "feedback_collected"

class PricingExperimentPydantic(BaseModel):
    product: Optional[ProductPydantic] = None
    experiment_number: Optional[int] = None
    experiment_gen_stage: Optional[ExperimentGenStage] = None
    objective: Optional[str] = None
    usecase: Optional[str] = None
    product_seed_context: Optional[str]=None
    relevant_segment: Optional[CustomerSegmentPydantic] = None
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
