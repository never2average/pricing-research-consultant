import uuid
import json
from deepresearch.product_offering import agent as product_offering_agent
from deepresearch.segmentwise_roi import agent as segmentwise_roi_agent
from deepresearch.pricing_analysis import agent as pricing_analysis_agent
from deepresearch.value_capture_analysis import agent as value_capture_analysis_agent
from deepresearch.experimental_pricing_recommendation import agent as experimental_pricing_recommendation_agent
from concurrent.futures import ThreadPoolExecutor
from datastore.models import OrchestrationResult
from datastore.orchestration_state import OrchestrationState, PricingAnalysisResponse, RecommendedPricingModelResponse
from tqdm import tqdm


def save_orchestration_step(invocation_id, step_name, step_order, product_id, step_input, step_output):
    """Helper function to save orchestration step results to MongoDB"""
    try:
        # Convert step_input to serializable format
        if hasattr(step_input, 'model_dump'):
            serializable_input = step_input.model_dump()
        elif hasattr(step_input, 'dict'):
            serializable_input = step_input.dict()
        elif isinstance(step_input, dict):
            serializable_input = step_input
        else:
            serializable_input = str(step_input)

        # Convert step_output to serializable format
        if hasattr(step_output, 'model_dump'):
            serializable_output = step_output.model_dump()
        elif hasattr(step_output, 'dict'):
            serializable_output = step_output.dict()
        elif isinstance(step_output, dict):
            serializable_output = step_output
        else:
            serializable_output = str(step_output)

        result = OrchestrationResult(
            invocation_id=invocation_id,
            step_name=step_name,
            step_order=step_order,
            product_id=str(product_id),
            step_input=serializable_input,
            step_output=serializable_output
        )
        result.save()
        print(f"Saved step {step_name} (order: {step_order}) for invocation {invocation_id}")
    except Exception as e:
        print(f"Error saving step {step_name}: {e}")


def final_agent(product_id, usage_scope=None, customer_segment_id=None):
    # Initialize orchestration state
    invocation_id = str(uuid.uuid4())
    state = OrchestrationState(
        invocation_id=invocation_id,
        product_id=product_id,
        usage_scope=usage_scope,
        customer_segment_id=customer_segment_id,
        total_steps=5
    )
    
    print(f"Starting orchestration with invocation ID: {invocation_id}")
    
    # Initialize progress bar for 5 main steps
    progress = tqdm(total=5, desc="Orchestration Progress", unit="step")
    
    try:
        # Step 1: Run product offering agent (must be first)
        progress.set_description("Step 1: Product offering analysis")
        product_offering_input = {
            "product_id": product_id,
            "usage_scope": usage_scope
        }
        
        state.start_step("product_offering", 1, product_offering_input)
        try:
            product_research = product_offering_agent(product_id, usage_scope)
            state.product_research = product_research
            state.complete_step("product_offering", product_research)
            save_orchestration_step(invocation_id, "product_offering", 1, product_id, product_offering_input, product_research)
            progress.update(1)
        except Exception as e:
            error_msg = f"Error in product offering analysis: {str(e)}"
            state.fail_step("product_offering", error_msg)
            print(error_msg)
            return state

        # Step 2: Run segmentwise ROI and pricing analysis in parallel
        progress.set_description("Step 2: Segmentwise ROI & pricing analysis (parallel)")

        def run_segment_roi():
            segment_roi_input = {
                "product_id": product_id,
                "product_research": product_research
            }
            state.start_step("segmentwise_roi", 2, segment_roi_input)
            try:
                result = segmentwise_roi_agent(product_id, product_research)
                state.segment_research = result
                state.complete_step("segmentwise_roi", result)
                save_orchestration_step(invocation_id, "segmentwise_roi", 2, product_id, segment_roi_input, result)
                return result
            except Exception as e:
                error_msg = f"Error in segmentwise ROI analysis: {str(e)}"
                state.fail_step("segmentwise_roi", error_msg)
                raise e

        def run_pricing_analysis():
            pricing_analysis_input = {
                "product_id": product_id
            }
            state.start_step("pricing_analysis", 3, pricing_analysis_input)
            try:
                result = pricing_analysis_agent(product_id)
                state.pricing_research = result
                state.complete_step("pricing_analysis", result)
                save_orchestration_step(invocation_id, "pricing_analysis", 3, product_id, pricing_analysis_input, result)
                return result
            except Exception as e:
                error_msg = f"Error in pricing analysis: {str(e)}"
                state.fail_step("pricing_analysis", error_msg)
                raise e

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            segment_future = executor.submit(run_segment_roi)
            pricing_future = executor.submit(run_pricing_analysis)

            try:
                # Wait for both to complete and get results
                segment_research = segment_future.result()
                pricing_research = pricing_future.result()
            except Exception as e:
                print(f"Error in parallel execution: {str(e)}")
                return state

        progress.update(1)

        # Step 3: Value capture analysis
        progress.set_description("Step 3: Value capture analysis")
        value_capture_input = {
            "segment_research": segment_research,
            "pricing_research": pricing_research,
            "product_research": product_research
        }
        
        state.start_step("value_capture_analysis", 4, value_capture_input)
        try:
            value_capture_research = value_capture_analysis_agent(segment_research, pricing_research, product_research)
            state.value_capture_research = value_capture_research
            state.complete_step("value_capture_analysis", value_capture_research)
            save_orchestration_step(invocation_id, "value_capture_analysis", 4, product_id, value_capture_input, value_capture_research)
            progress.update(1)
        except Exception as e:
            error_msg = f"Error in value capture analysis: {str(e)}"
            state.fail_step("value_capture_analysis", error_msg)
            print(error_msg)
            return state

        # Step 4: Experimental pricing recommendation
        progress.set_description("Step 4: Experimental pricing recommendation")
        experimental_pricing_input = {
            "product_id": product_id,
            "value_capture_research": value_capture_research
        }
        
        state.start_step("experimental_pricing_recommendation", 5, experimental_pricing_input)
        try:
            experimental_pricing_research = experimental_pricing_recommendation_agent(product_id, value_capture_research)
            
            # Store both raw result and structured data
            state.experimental_pricing_research = json.dumps(experimental_pricing_research) if isinstance(experimental_pricing_research, dict) else str(experimental_pricing_research)
            
            # Extract structured data if available
            if isinstance(experimental_pricing_research, dict):
                pricing_response = experimental_pricing_research.get('pricing_response')
                if pricing_response:
                    if hasattr(pricing_response, 'model_dump'):
                        state.experimental_pricing_structured = RecommendedPricingModelResponse(**pricing_response.model_dump())
                    elif isinstance(pricing_response, dict):
                        state.experimental_pricing_structured = RecommendedPricingModelResponse(**pricing_response)
                
                # Store generated IDs
                state.pricing_model_id = experimental_pricing_research.get('pricing_model_id')
                state.customer_segment_ids = experimental_pricing_research.get('customer_segment_ids', [])
                state.recommended_pricing_id = experimental_pricing_research.get('recommended_pricing_id')
                state.recommended_pricing_ids = experimental_pricing_research.get('recommended_pricing_ids', [])
            
            state.complete_step("experimental_pricing_recommendation", experimental_pricing_research)
            save_orchestration_step(invocation_id, "experimental_pricing_recommendation", 5, product_id, experimental_pricing_input, experimental_pricing_research)
            progress.update(1)
        except Exception as e:
            error_msg = f"Error in experimental pricing recommendation: {str(e)}"
            state.fail_step("experimental_pricing_recommendation", error_msg)
            print(error_msg)
            return state

        # Display results if available
        try:
            if state.experimental_pricing_structured:
                display_pricing_recommendations(state.experimental_pricing_structured)
        except Exception as e:
            print(f"Error displaying recommendations: {str(e)}")

        progress.set_description("Orchestration completed!")
        progress.close()
        print(f"Orchestration completed. Invocation ID: {invocation_id}")
        print(f"Progress: {state.get_progress_percentage():.1f}% ({len(state.get_completed_steps())}/{state.total_steps} steps completed)")
        
        return state
        
    except Exception as e:
        print(f"Unexpected error in orchestration: {str(e)}")
        progress.close()
        return state


def display_pricing_recommendations(pricing_response: RecommendedPricingModelResponse):
    """Display pricing recommendations in a formatted way"""
    try:
        lines = []
        lines.append("### Recommended Pricing Model")
        lines.append(f"- **Plan name**: {pricing_response.plan_name}")
        lines.append(f"- **Unit price**: {pricing_response.unit_price}")
        lines.append(f"- **Min unit count**: {pricing_response.min_unit_count}")
        lines.append(f"- **Unit calculation logic**: {pricing_response.unit_calculation_logic}")
        lines.append(f"- **Min unit utilization period**: {pricing_response.min_unit_utilization_period}")
        
        for idx, seg in enumerate(pricing_response.recommended_customer_segment, start=1):
            lines.append("")
            lines.append(f"### Segment {idx}")
            lines.append(f"- **Existing**: {seg.existing_customer_segment}")
            if seg.customer_segment_uid:
                lines.append(f"- **Customer segment uid**: {seg.customer_segment_uid}")
            if seg.customer_segment_name:
                lines.append(f"- **Customer segment name**: {seg.customer_segment_name}")
            if seg.customer_segment_description:
                lines.append(f"- **Customer segment description**: {seg.customer_segment_description}")
            
            if seg.projection:
                lines.append("")
                lines.append("| date | revenue | margin | profit | customer_count |")
                lines.append("|---|---:|---:|---:|---:|")
                for fp in seg.projection:
                    lines.append(f"| {fp.date} | {fp.revenue} | {fp.margin} | {fp.profit} | {fp.customer_count} |")
        
        print("\n".join(lines))
    except Exception as e:
        print(f"Error displaying recommendations: {str(e)}")
    
