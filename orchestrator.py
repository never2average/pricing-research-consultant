import uuid
import json
from deepresearch.product_offering import agent as product_offering_agent
from deepresearch.segmentwise_roi import agent as segmentwise_roi_agent
from deepresearch.pricing_analysis import agent as pricing_analysis_agent
from deepresearch.value_capture_analysis import agent as value_capture_analysis_agent
from deepresearch.experimental_pricing_recommendation import agent as experimental_pricing_recommendation_agent
from concurrent.futures import ThreadPoolExecutor
from datastore.models import OrchestrationResult
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

    # Generate unique invocation ID
    invocation_id = str(uuid.uuid4())
    print(f"Starting orchestration with invocation ID: {invocation_id}")

    # Initialize progress bar for 4 main steps
    progress = tqdm(total=4, desc="Orchestration Progress", unit="step")

    # Step 1: Run product offering agent (must be first)
    progress.set_description("Step 1: Product offering analysis")
    product_offering_input = {
        "product_id": product_id,
        "usage_scope": usage_scope
    }
    product_research = product_offering_agent(product_id, usage_scope)
    save_orchestration_step(invocation_id, "product_offering", 1, product_id, product_offering_input, product_research)
    progress.update(1)

    # Step 2: Run segmentwise ROI and pricing analysis in parallel
    progress.set_description("Step 2: Segmentwise ROI & pricing analysis (parallel)")

    def run_segment_roi():
        segment_roi_input = {
            "product_id": product_id,
            "product_research": product_research
        }
        result = segmentwise_roi_agent(product_id, product_research)
        save_orchestration_step(invocation_id, "segmentwise_roi", 2, product_id, segment_roi_input, result)
        return result

    def run_pricing_analysis():
        pricing_analysis_input = {
            "product_id": product_id
        }
        result = pricing_analysis_agent(product_id)
        save_orchestration_step(invocation_id, "pricing_analysis", 3, product_id, pricing_analysis_input, result)
        return result

    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both tasks
        segment_future = executor.submit(run_segment_roi)
        pricing_future = executor.submit(run_pricing_analysis)

        # Wait for both to complete and get results
        segment_research = segment_future.result()
        pricing_research = pricing_future.result()

    progress.update(1)

    # Step 3: Run remaining agents sequentially
    progress.set_description("Step 3: Value capture analysis")
    value_capture_input = {
        "segment_research": segment_research,
        "pricing_research": pricing_research,
        "product_research": product_research
    }
    value_capture_research = value_capture_analysis_agent(segment_research, pricing_research, product_research)
    save_orchestration_step(invocation_id, "value_capture_analysis", 4, product_id, value_capture_input, value_capture_research)
    progress.update(1)

    progress.set_description("Step 4: Experimental pricing recommendation")
    experimental_pricing_input = {
        "product_id": product_id,
        "value_capture_research": value_capture_research
    }
    experimental_pricing_research = experimental_pricing_recommendation_agent(product_id, value_capture_research)
    save_orchestration_step(invocation_id, "experimental_pricing_recommendation", 5, product_id, experimental_pricing_input, experimental_pricing_research)
    progress.update(1)

    pr = None
    try:
        pr = experimental_pricing_research.get('pricing_response')
    except Exception:
        pr = None

    if pr is not None:
        try:
            if hasattr(pr, 'model_dump'):
                data = pr.model_dump()
            elif hasattr(pr, 'dict'):
                data = pr.dict()
            else:
                data = pr
            lines = []
            lines.append("### Recommended Pricing Model")
            plan_name = data.get('plan_name')
            unit_price = data.get('unit_price')
            min_unit_count = data.get('min_unit_count')
            unit_calc = data.get('unit_calculation_logic')
            min_util = data.get('min_unit_utilization_period')
            if plan_name is not None:
                lines.append(f"- **Plan name**: {plan_name}")
            if unit_price is not None:
                lines.append(f"- **Unit price**: {unit_price}")
            if min_unit_count is not None:
                lines.append(f"- **Min unit count**: {min_unit_count}")
            if unit_calc is not None:
                lines.append(f"- **Unit calculation logic**: {unit_calc}")
            if min_util is not None:
                lines.append(f"- **Min unit utilization period**: {min_util}")
            segs = data.get('recommended_customer_segment') or []
            for idx, seg in enumerate(segs, start=1):
                lines.append("")
                lines.append(f"### Segment {idx}")
                ecs = seg.get('existing_customer_segment')
                cs_uid = seg.get('customer_segment_uid')
                cs_name = seg.get('customer_segment_name')
                cs_desc = seg.get('customer_segment_description')
                lines.append(f"- **Existing**: {ecs}")
                if cs_uid:
                    lines.append(f"- **Customer segment uid**: {cs_uid}")
                if cs_name:
                    lines.append(f"- **Customer segment name**: {cs_name}")
                if cs_desc:
                    lines.append(f"- **Customer segment description**: {cs_desc}")
                proj = seg.get('projection') or []
                if proj:
                    lines.append("")
                    lines.append("| date | revenue | margin | profit | customer_count |")
                    lines.append("|---|---:|---:|---:|---:|")
                    for fp in proj:
                        date = fp.get('date')
                        revenue = fp.get('revenue')
                        margin = fp.get('margin')
                        profit = fp.get('profit')
                        cc = fp.get('customer_count')
                        lines.append(f"| {date} | {revenue} | {margin} | {profit} | {cc} |")
            print("\n".join(lines))
        except Exception:
            try:
                print(str(pr))
            except Exception:
                pass

    progress.set_description("Orchestration completed!")
    progress.close()
    print(f"Orchestration completed. Invocation ID: {invocation_id}")
    return invocation_id
    
