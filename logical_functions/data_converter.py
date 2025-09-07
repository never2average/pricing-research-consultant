from datastore.types import PricingExperimentPydantic
from datastore.models import PricingExperimentRuns

def convert_to_pydantic(experiment_run: PricingExperimentRuns):
    segments = []
    if experiment_run.relevant_segment:
        seg = experiment_run.relevant_segment
        segments.append({
            "segment_name": seg.segment_name,
            "segment_cdp_uid": seg.segment_cdp_uid,
            "segment_description": seg.segment_description,
            "segment_filter_logic": seg.segment_filter_logic,
            "segment_usage_summary": seg.segment_usage_summary,
            "segment_revenue_attribution_summary": seg.segment_revenue_attribution_summary
        })
    
    product_data = {}
    if experiment_run.experiment_request.product:
        product_data = {
            "product_name": experiment_run.experiment_request.product.product_name,
            "product_industry": experiment_run.experiment_request.product.product_industry,
            "product_description": experiment_run.experiment_request.product.product_description,
            "product_icp_summary": experiment_run.experiment_request.product.product_icp_summary,
            "product_categories": experiment_run.experiment_request.product.product_categories,
            "product_categories_vs_id": experiment_run.experiment_request.product.product_categories_vs_id,
            "product_feature_docs": experiment_run.experiment_request.product.product_feature_docs,
            "product_feature_docs_vs_id": experiment_run.experiment_request.product.product_feature_docs_vs_id,
            "product_marketing_docs": experiment_run.experiment_request.product.product_marketing_docs,
            "product_marketing_docs_vs_id": experiment_run.experiment_request.product.product_marketing_docs_vs_id,
            "product_technical_docs": experiment_run.experiment_request.product.product_technical_docs,
            "product_technical_docs_vs_id": experiment_run.experiment_request.product.product_technical_docs_vs_id
        }
    
    usage_proj = []
    if experiment_run.usage_projections:
        for proj in experiment_run.usage_projections:
            usage_proj.append({
                "usage_value_in_units": proj.usage_value_in_units,
                "usage_unit": proj.usage_unit,
                "target_date": proj.target_date
            })
            
    revenue_proj = []
    if experiment_run.revenue_projections:
        for proj in experiment_run.revenue_projections:
            revenue_proj.append({
                "usage_value_in_units": proj.usage_value_in_units,
                "usage_unit": proj.usage_unit,
                "target_date": proj.target_date
            })
    
    return PricingExperimentPydantic(
        product=product_data if product_data else None,
        experiment_number=experiment_run.experiment_request.experiment_number,
        experiment_gen_stage=experiment_run.experiment_gen_stage,
        objective=experiment_run.experiment_request.objective,
        usecase=experiment_run.experiment_request.usecase,
        relevant_segments=segments if segments else None,
        positioning_summary=experiment_run.positioning_summary,
        usage_summary=experiment_run.usage_summary,
        roi_gaps=experiment_run.roi_gaps,
        experimental_pricing_plan=experiment_run.experimental_pricing_plan,
        simulation_result=experiment_run.simulation_result,
        usage_projections=usage_proj if usage_proj else None,
        revenue_projections=revenue_proj if revenue_proj else None,
        cashflow_feasibility_comments=experiment_run.cashflow_feasibility_comments,
        cashflow_no_negative_impact_approval_given=experiment_run.cashflow_no_negative_impact_approval_given,
        experiment_is_deployed=experiment_run.experiment_is_deployed,
        experiment_deployed_on=experiment_run.experiment_deployed_on,
        experiment_feedback_summary=experiment_run.experiment_feedback_summary
    )
