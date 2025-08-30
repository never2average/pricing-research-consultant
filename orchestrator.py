from deepresearch.product_offering import agent as product_offering_agent
from deepresearch.segmentwise_roi import agent as segmentwise_roi_agent
from deepresearch.pricing_analysis import agent as pricing_analysis_agent
from deepresearch.value_capture_analysis import agent as value_capture_analysis_agent
from deepresearch.experimental_pricing_recommendation import agent as experimental_pricing_recommendation_agent


def final_agent(product_id, usage_scope=None, customer_segment_id=None):
    product_research = product_offering_agent(product_id, usage_scope)
    segment_research = segmentwise_roi_agent(product_id, product_research)
    pricing_research = pricing_analysis_agent(product_id)
    value_capture_research = value_capture_analysis_agent(segment_research, pricing_research, product_research)
    experimental_pricing_research = experimental_pricing_recommendation_agent(product_id, value_capture_research)
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
            unit_price = data.get('unit_price')
            min_unit_count = data.get('min_unit_count')
            unit_calc = data.get('unit_calculation_logic')
            min_util = data.get('min_unit_utilization_period')
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
    
