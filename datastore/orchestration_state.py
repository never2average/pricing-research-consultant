from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed" 
    FAILED = "failed"

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
    forecasts: List[SegmentPlanForecast] = Field(default_factory=list)

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
    projection: List[ForwardProjections] = Field(default_factory=list)

class RecommendedPricingModelResponse(BaseModel):
    recommended_customer_segment: List[RecommendedCustomerSegmentModel] = Field(default_factory=list)
    plan_name: str = Field(default="Recommended Plan")
    unit_price: float
    min_unit_count: int
    unit_calculation_logic: str
    min_unit_utilization_period: str

class StepResult(BaseModel):
    step_name: str
    step_order: int
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    step_input: Dict[str, Any] = Field(default_factory=dict)
    step_output: Optional[Union[str, Dict[str, Any]]] = None

class OrchestrationState(BaseModel):
    # Metadata
    invocation_id: str
    product_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Initial inputs
    usage_scope: Optional[str] = None
    customer_segment_id: Optional[str] = None
    
    # Step tracking
    current_step: int = 0
    total_steps: int = 5
    steps: Dict[str, StepResult] = Field(default_factory=dict)
    
    # Agent outputs (raw text)
    product_research: Optional[str] = None
    segment_research: Optional[str] = None 
    pricing_research: Optional[str] = None
    value_capture_research: Optional[str] = None
    experimental_pricing_research: Optional[str] = None
    
    # Structured outputs from specific agents
    pricing_analysis_structured: Optional[PricingAnalysisResponse] = None
    experimental_pricing_structured: Optional[RecommendedPricingModelResponse] = None
    
    # Generated IDs from experimental pricing
    pricing_model_id: Optional[str] = None
    customer_segment_ids: List[str] = Field(default_factory=list)
    recommended_pricing_id: Optional[str] = None
    recommended_pricing_ids: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
    
    def update_timestamp(self):
        self.updated_at = datetime.utcnow()
    
    def start_step(self, step_name: str, step_order: int, step_input: Dict[str, Any]):
        self.steps[step_name] = StepResult(
            step_name=step_name,
            step_order=step_order,
            status=StepStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
            step_input=step_input
        )
        self.current_step = step_order
        self.update_timestamp()
    
    def complete_step(self, step_name: str, step_output: Union[str, Dict[str, Any]]):
        if step_name in self.steps:
            self.steps[step_name].status = StepStatus.COMPLETED
            self.steps[step_name].completed_at = datetime.utcnow()
            self.steps[step_name].step_output = step_output
            self.update_timestamp()
    
    def fail_step(self, step_name: str, error_message: str):
        if step_name in self.steps:
            self.steps[step_name].status = StepStatus.FAILED
            self.steps[step_name].completed_at = datetime.utcnow()
            self.steps[step_name].error_message = error_message
            self.update_timestamp()
    
    def get_step_status(self, step_name: str) -> Optional[StepStatus]:
        return self.steps.get(step_name, {}).status if step_name in self.steps else None
    
    def is_step_completed(self, step_name: str) -> bool:
        return self.get_step_status(step_name) == StepStatus.COMPLETED
    
    def get_completed_steps(self) -> List[str]:
        return [
            step_name for step_name, step_result in self.steps.items() 
            if step_result.status == StepStatus.COMPLETED
        ]
    
    def get_failed_steps(self) -> List[str]:
        return [
            step_name for step_name, step_result in self.steps.items()
            if step_result.status == StepStatus.FAILED
        ]
    
    def is_orchestration_complete(self) -> bool:
        required_steps = [
            "product_offering",
            "segmentwise_roi", 
            "pricing_analysis",
            "value_capture_analysis",
            "experimental_pricing_recommendation"
        ]
        return all(self.is_step_completed(step) for step in required_steps)
    
    def get_progress_percentage(self) -> float:
        if self.total_steps == 0:
            return 0.0
        completed_count = len(self.get_completed_steps())
        return (completed_count / self.total_steps) * 100.0
    
    def to_orchestration_result_dict(self) -> Dict[str, Any]:
        """Convert state to format compatible with OrchestrationResult model"""
        return {
            "invocation_id": self.invocation_id,
            "product_id": self.product_id,
            "steps": {
                step_name: {
                    "step_name": step_result.step_name,
                    "step_order": step_result.step_order,
                    "status": step_result.status,
                    "step_input": step_result.step_input,
                    "step_output": step_result.step_output,
                    "started_at": step_result.started_at,
                    "completed_at": step_result.completed_at,
                    "error_message": step_result.error_message
                }
                for step_name, step_result in self.steps.items()
            },
            "agent_outputs": {
                "product_research": self.product_research,
                "segment_research": self.segment_research,
                "pricing_research": self.pricing_research,
                "value_capture_research": self.value_capture_research,
                "experimental_pricing_research": self.experimental_pricing_research
            },
            "structured_outputs": {
                "pricing_analysis_structured": self.pricing_analysis_structured.model_dump() if self.pricing_analysis_structured else None,
                "experimental_pricing_structured": self.experimental_pricing_structured.model_dump() if self.experimental_pricing_structured else None
            },
            "generated_ids": {
                "pricing_model_id": self.pricing_model_id,
                "customer_segment_ids": self.customer_segment_ids,
                "recommended_pricing_id": self.recommended_pricing_id,
                "recommended_pricing_ids": self.recommended_pricing_ids
            },
            "metadata": {
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "current_step": self.current_step,
                "total_steps": self.total_steps,
                "progress_percentage": self.get_progress_percentage(),
                "is_complete": self.is_orchestration_complete()
            }
        }

class OrchestrationStateManager:
    """Utility class for managing orchestration state across agents"""
    
    @staticmethod
    def create_initial_state(product_id: str, usage_scope: Optional[str] = None, customer_segment_id: Optional[str] = None) -> OrchestrationState:
        """Create a new orchestration state with initial parameters"""
        import uuid
        return OrchestrationState(
            invocation_id=str(uuid.uuid4()),
            product_id=product_id,
            usage_scope=usage_scope,
            customer_segment_id=customer_segment_id,
            total_steps=5
        )
    
    @staticmethod
    def get_agent_inputs(state: OrchestrationState, agent_name: str) -> Dict[str, Any]:
        """Get the required inputs for a specific agent based on current state"""
        inputs = {"product_id": state.product_id}
        
        if agent_name == "product_offering":
            if state.usage_scope:
                inputs["usage_scope"] = state.usage_scope
                
        elif agent_name == "segmentwise_roi":
            if state.product_research:
                inputs["product_research"] = state.product_research
            else:
                raise ValueError("Product research not available for segmentwise ROI agent")
                
        elif agent_name == "pricing_analysis":
            # Pricing analysis only needs product_id which is already included
            pass
            
        elif agent_name == "value_capture_analysis":
            if not all([state.segment_research, state.pricing_research, state.product_research]):
                missing = []
                if not state.segment_research:
                    missing.append("segment_research")
                if not state.pricing_research:
                    missing.append("pricing_research")
                if not state.product_research:
                    missing.append("product_research")
                raise ValueError(f"Missing required inputs for value capture analysis: {', '.join(missing)}")
            
            inputs = {
                "segment_roi_analysis": state.segment_research,
                "pricing_analysis": state.pricing_research,
                "product_research": state.product_research
            }
            
        elif agent_name == "experimental_pricing_recommendation":
            if not state.value_capture_research:
                raise ValueError("Value capture research not available for experimental pricing recommendation")
            inputs = {
                "product_id": state.product_id,
                "value_capture_analysis": state.value_capture_research
            }
        
        return inputs
    
    @staticmethod
    def validate_state_for_agent(state: OrchestrationState, agent_name: str) -> bool:
        """Validate that the state has all required data for an agent"""
        try:
            OrchestrationStateManager.get_agent_inputs(state, agent_name)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def get_next_executable_agents(state: OrchestrationState) -> List[str]:
        """Get list of agents that can be executed based on current state"""
        executable = []
        
        # Product offering can always run if not completed
        if not state.is_step_completed("product_offering"):
            executable.append("product_offering")
        
        # Segmentwise ROI and pricing analysis can run in parallel after product offering
        if state.is_step_completed("product_offering"):
            if not state.is_step_completed("segmentwise_roi"):
                executable.append("segmentwise_roi")
            if not state.is_step_completed("pricing_analysis"):
                executable.append("pricing_analysis")
        
        # Value capture analysis needs both segmentwise ROI and pricing analysis
        if (state.is_step_completed("segmentwise_roi") and 
            state.is_step_completed("pricing_analysis") and 
            not state.is_step_completed("value_capture_analysis")):
            executable.append("value_capture_analysis")
        
        # Experimental pricing recommendation needs value capture analysis
        if (state.is_step_completed("value_capture_analysis") and 
            not state.is_step_completed("experimental_pricing_recommendation")):
            executable.append("experimental_pricing_recommendation")
        
        return executable
    
    @staticmethod
    def get_state_summary(state: OrchestrationState) -> Dict[str, Any]:
        """Get a summary of the current state"""
        return {
            "invocation_id": state.invocation_id,
            "product_id": state.product_id,
            "progress": {
                "current_step": state.current_step,
                "total_steps": state.total_steps,
                "percentage": state.get_progress_percentage(),
                "completed_steps": state.get_completed_steps(),
                "failed_steps": state.get_failed_steps(),
                "is_complete": state.is_orchestration_complete()
            },
            "data_availability": {
                "product_research": bool(state.product_research),
                "segment_research": bool(state.segment_research),
                "pricing_research": bool(state.pricing_research),
                "value_capture_research": bool(state.value_capture_research),
                "experimental_pricing_research": bool(state.experimental_pricing_research),
                "experimental_pricing_structured": bool(state.experimental_pricing_structured)
            },
            "next_executable_agents": OrchestrationStateManager.get_next_executable_agents(state),
            "created_at": state.created_at,
            "updated_at": state.updated_at
        }
    
    @staticmethod
    def save_state_to_mongodb(state: OrchestrationState):
        """Save the current state to MongoDB using OrchestrationResult model"""
        from .models import OrchestrationResult
        
        state_dict = state.to_orchestration_result_dict()
        
        # Save overall state
        overall_result = OrchestrationResult(
            invocation_id=state.invocation_id,
            step_name="orchestration_state",
            step_order=0,
            product_id=state.product_id,
            step_input={"initial_params": {
                "usage_scope": state.usage_scope,
                "customer_segment_id": state.customer_segment_id
            }},
            step_output=state_dict
        )
        overall_result.save()
        
        return overall_result.id
    
    @staticmethod
    def load_state_from_mongodb(invocation_id: str) -> Optional[OrchestrationState]:
        """Load orchestration state from MongoDB"""
        from .models import OrchestrationResult
        
        try:
            overall_result = OrchestrationResult.objects(
                invocation_id=invocation_id,
                step_name="orchestration_state"
            ).first()
            
            if not overall_result or not overall_result.step_output:
                return None
            
            state_data = overall_result.step_output
            
            # Reconstruct the state
            state = OrchestrationState(
                invocation_id=invocation_id,
                product_id=state_data.get("product_id"),
                created_at=state_data.get("metadata", {}).get("created_at"),
                updated_at=state_data.get("metadata", {}).get("updated_at"),
                current_step=state_data.get("metadata", {}).get("current_step", 0),
                total_steps=state_data.get("metadata", {}).get("total_steps", 5)
            )
            
            # Restore agent outputs
            agent_outputs = state_data.get("agent_outputs", {})
            state.product_research = agent_outputs.get("product_research")
            state.segment_research = agent_outputs.get("segment_research") 
            state.pricing_research = agent_outputs.get("pricing_research")
            state.value_capture_research = agent_outputs.get("value_capture_research")
            state.experimental_pricing_research = agent_outputs.get("experimental_pricing_research")
            
            # Restore structured outputs
            structured_outputs = state_data.get("structured_outputs", {})
            if structured_outputs.get("experimental_pricing_structured"):
                state.experimental_pricing_structured = RecommendedPricingModelResponse(
                    **structured_outputs["experimental_pricing_structured"]
                )
            
            # Restore generated IDs
            generated_ids = state_data.get("generated_ids", {})
            state.pricing_model_id = generated_ids.get("pricing_model_id")
            state.customer_segment_ids = generated_ids.get("customer_segment_ids", [])
            state.recommended_pricing_id = generated_ids.get("recommended_pricing_id")
            state.recommended_pricing_ids = generated_ids.get("recommended_pricing_ids", [])
            
            # Restore step results
            steps_data = state_data.get("steps", {})
            for step_name, step_data in steps_data.items():
                step_result = StepResult(**step_data)
                state.steps[step_name] = step_result
            
            return state
            
        except Exception as e:
            print(f"Error loading state from MongoDB: {str(e)}")
            return None
