from deepresearch.product_offering import agent as product_offering_agent
from deepresearch.segmentwise_roi import agent as segmentwise_roi_agent
from deepresearch.pricing_analysis import agent as pricing_analysis_agent
from deepresearch.value_capture_analysis import agent as value_capture_analysis_agent
from deepresearch.experimental_pricing_recommendation import agent as experimental_pricing_recommendation_agent
from datastore.models import

def final_agent(product_id, usage_scope=None, customer_segment_id=None):
    product_research = product_offering_agent(product_id, usage_scope)
    segment_research = segmentwise_roi_agent(product_id)
    pricing_research = pricing_analysis_agent(product_id)
    value_capture_research = value_capture_analysis_agent(segment_research, pricing_research)
    experimental_pricing_research = experimental_pricing_recommendation_agent(product_id, value_capture_research)
    
    return {
        'product_research': product_research,
        'segment_research': segment_research,
        'pricing_research': pricing_research,
        'value_capture_research': value_capture_research,
        'experimental_pricing_research': experimental_pricing_research
    }
