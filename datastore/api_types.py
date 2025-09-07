from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum


class CustomerSegmentAPI(BaseModel):
    _id: Optional[str] = None
    product: Optional[str] = None
    customer_segment_uid: str
    customer_segment_name: str
    customer_segment_description: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PricingPlanAPI(BaseModel):
    _id: Optional[str] = None
    plan_name: str
    unit_price: float
    min_unit_count: int
    unit_calculation_logic: str
    min_unit_utilization_period: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CompetitorAPI(BaseModel):
    competitor_name: str
    website_url: str
    product_description: str


class ProductAPI(BaseModel):
    _id: Optional[str] = None
    name: str
    icp_description: Optional[str] = None
    unit_level_cogs: Optional[str] = None
    features_description_summary: Optional[str] = None
    competitors: Optional[List[CompetitorAPI]] = None
    product_documentations: Optional[List[str]] = None
    vector_store_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ConnectionType(str, Enum):
    FINALIZED = "finalized"
    EXPERIMENTAL = "experimental"


class SegmentPlanLinkAPI(BaseModel):
    _id: Optional[str] = None
    customer_segment_id: str
    pricing_plan_id: str
    connection_type: ConnectionType
    percentage: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_active: Optional[bool] = None


class SegmentPlanLinkWithDetailsAPI(SegmentPlanLinkAPI):
    customer_segment: Optional[CustomerSegmentAPI] = None
    pricing_plan: Optional[PricingPlanAPI] = None


class SearchResultType(str, Enum):
    CUSTOMER_SEGMENT = "customer_segment"
    PRICING_PLAN = "pricing_plan"
    PRODUCT = "product"
    OTHER = "other"


class SearchResultAPI(BaseModel):
    type: SearchResultType
    id: str
    title: str
    description: str
    score: Optional[float] = None


class SearchResponseAPI(BaseModel):
    results: List[SearchResultAPI]
    total_count: int
    query: str


class ReportSectionAPI(BaseModel):
    id: str
    name: str
    prompt: str
    section_type: Optional[str] = None


class ScheduledReportStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class ScheduledReportAPI(BaseModel):
    _id: Optional[str] = None
    name: str
    schedule_type: str
    schedule_config: Any
    report_sections: List[ReportSectionAPI]
    recipients: List[str]
    created_at: Optional[str] = None
    status: Optional[ScheduledReportStatus] = None


class HistoricalRunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ProgressAPI(BaseModel):
    completed_steps: int
    total_steps: int
    current_step: Optional[str] = None


class HistoricalRunAPI(BaseModel):
    _id: Optional[str] = None
    invocation_id: str
    task_type: str
    task_name: str
    status: HistoricalRunStatus
    started_at: str
    completed_at: Optional[str] = None
    duration: Optional[str] = None
    participants: Optional[int] = None
    conversion: Optional[str] = None
    task_details: str
    progress: Optional[ProgressAPI] = None


class RunLogLevel(str, Enum):
    INFO = "INFO"
    ERROR = "ERROR"
    WARNING = "WARNING"
    DEBUG = "DEBUG"


class RunLogAPI(BaseModel):
    timestamp: str
    level: RunLogLevel
    message: str
    step_name: Optional[str] = None
    details: Optional[Any] = None


class RunLogsResponseAPI(BaseModel):
    invocation_id: str
    logs: List[RunLogAPI]
    status: str


class ProductIntegrationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class ProductIntegrationAPI(BaseModel):
    _id: Optional[str] = None
    product_id: str
    integration_type: str
    config: Any
    status: ProductIntegrationStatus
    created_at: Optional[str] = None


class DataSourceConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class DataSourceAPI(BaseModel):
    _id: Optional[str] = None
    name: str
    source_type: str
    connection_status: DataSourceConnectionStatus
    last_sync: Optional[str] = None
    config: Optional[Any] = None


class ServiceStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class EnvironmentConfigAPI(BaseModel):
    openai_api_key_configured: bool
    database_connected: bool
    vector_store_enabled: bool
    services_status: Dict[str, ServiceStatus]


class LLMTextConfigAPI(BaseModel):
    system_prompts: Dict[str, str]
    analysis_templates: Dict[str, str]
    response_formats: Dict[str, Any]


class AutomationConfigAPI(BaseModel):
    _id: Optional[str] = None
    name: str
    automation_type: str
    trigger_config: Any
    action_config: Any
    is_active: bool
    last_run: Optional[str] = None
    next_run: Optional[str] = None


class WorkflowType(str, Enum):
    PRICING_ANALYSIS = "pricing_analysis"
    CUSTOMER_SEGMENTATION = "customer_segmentation"
    REVENUE_FORECAST = "revenue_forecast"
    FULL_ANALYSIS = "full_analysis"


class AnalysisDepth(str, Enum):
    BASIC = "basic"
    COMPREHENSIVE = "comprehensive"


class OrchestrationRequestAPI(BaseModel):
    workflow_type: WorkflowType
    product_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class OrchestrationStatus(str, Enum):
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OrchestrationResponseAPI(BaseModel):
    invocation_id: str
    status: OrchestrationStatus
    message: str


class CanvasNodeType(str, Enum):
    CUSTOMER_SEGMENT = "customerSegment"
    PRICING_PLAN = "pricingPlan"


class CanvasNodeDataAPI(BaseModel):
    id: str
    label: str
    type: CanvasNodeType
    segment_id: Optional[str] = None
    plan_id: Optional[str] = None


class CanvasPositionAPI(BaseModel):
    x: float
    y: float


class CanvasNodeAPI(BaseModel):
    data: CanvasNodeDataAPI
    position: CanvasPositionAPI


class CanvasEdgeDataAPI(BaseModel):
    id: str
    source: str
    target: str
    connectionType: ConnectionType
    percentage: Optional[str] = None
    link_id: Optional[str] = None


class CanvasEdgeAPI(BaseModel):
    data: CanvasEdgeDataAPI


class CanvasDataAPI(BaseModel):
    nodes: List[CanvasNodeAPI]
    edges: List[CanvasEdgeAPI]


class RevenueTimeSeriesDataAPI(BaseModel):
    date: str
    value: float


class SegmentRevenueDataAPI(BaseModel):
    segment_id: str
    segment_name: str
    revenue_data: List[RevenueTimeSeriesDataAPI]
    active_subscriptions: List[RevenueTimeSeriesDataAPI]
    forecast_data: Optional[List[RevenueTimeSeriesDataAPI]] = None


class SegmentContributionAPI(BaseModel):
    segment_id: str
    segment_name: str
    contribution_percentage: float
    revenue: float


class PlanRevenueDataAPI(BaseModel):
    plan_id: str
    plan_name: str
    revenue_data: List[RevenueTimeSeriesDataAPI]
    segment_contributions: List[SegmentContributionAPI]


class APIErrorAPI(BaseModel):
    error: str
    message: str
    details: Optional[Any] = None


class APIResponseAPI(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[APIErrorAPI] = None


class ListResponseAPI(BaseModel):
    items: List[Any]
    total_count: int
    page: Optional[int] = None
    page_size: Optional[int] = None


class HealthCheckResponseAPI(BaseModel):
    status: str
    timestamp: str


class SuccessResponseAPI(BaseModel):
    success: bool


class CreateSegmentPlanLinkRequestAPI(BaseModel):
    customer_segment_id: str
    pricing_plan_id: str
    connection_type: ConnectionType


class UpdateSegmentPlanLinkRequestAPI(BaseModel):
    id: str
    customer_segment_id: Optional[str] = None
    pricing_plan_id: Optional[str] = None
    connection_type: Optional[ConnectionType] = None
    percentage: Optional[float] = None
    is_active: Optional[bool] = None


class DeleteRequestAPI(BaseModel):
    id: str


class SearchRequestAPI(BaseModel):
    query: str


class CreateScheduledReportRequestAPI(BaseModel):
    name: str
    schedule_type: str
    schedule_config: Any
    sections: List[ReportSectionAPI]
    recipients: Optional[List[str]] = None


class CreateProductIntegrationRequestAPI(BaseModel):
    product_id: str
    integration_type: str
    config: Any


class CreateCanvasConnectionRequestAPI(BaseModel):
    customer_segment_id: str
    pricing_plan_id: str
    connection_type: ConnectionType


class CreateCanvasConnectionResponseAPI(BaseModel):
    success: bool
    connection_id: str
