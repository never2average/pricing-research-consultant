from utils.openai_client import openai_client, litellm_client
from datastore.models import Product, CustomerSegment, ProductPricingModel, CustomerUsageAnalysis
from .prompts import roi_prompt
from bson.objectid import ObjectId


def format_segments_table(segments):
    if not segments:
        return "No customer segments found."
    
    table = "| Segment UID | Segment Name | Description |\n"
    table += "|-------------|--------------|-------------|\n"
    
    for segment in segments:
        uid = segment.customer_segment_uid or "N/A"
        name = segment.customer_segment_name or "N/A"
        description = segment.customer_segment_description or "N/A"
        table += f"| {uid} | {name} | {description} |\n"
    
    return table


def format_usage_analysis_table(usage_analyses):
    if not usage_analyses:
        return "No usage analyses found."
    
    table = "| Customer UID | Segment | Task Description | Satisfaction Score | Reasoning |\n"
    table += "|--------------|---------|------------------|-------------------|----------|\n"
    
    for analysis in usage_analyses:
        customer_uid = analysis.customer_uid or "N/A"
        segment_name = analysis.customer_segment.customer_segment_name if analysis.customer_segment else "N/A"
        task = analysis.customer_task_to_agent or "N/A"
        satisfaction = analysis.predicted_customer_satisfaction_response or "N/A"
        reasoning = analysis.predicted_customer_satisfaction_response_reasoning or "N/A"
        
        # Truncate long text for table readability
        task = task[:50] + "..." if len(task) > 50 else task
        reasoning = reasoning[:100] + "..." if len(reasoning) > 100 else reasoning
        
        table += f"| {customer_uid} | {segment_name} | {task} | {satisfaction} | {reasoning} |\n"
    
    return table


def agent(product_id, product_research):
    all_segments = CustomerSegment.objects(product=ObjectId(product_id)).all()
    all_usage_analysis = CustomerUsageAnalysis.objects(product=ObjectId(product_id)).all()

    segments_table = format_segments_table(all_segments)
    usage_analysis_table = format_usage_analysis_table(all_usage_analysis)

    input_text = f"""
## Product Research Context
{product_research}

---
## Customer Segments Data
{segments_table}

---
## Customer Usage Analysis Data
{usage_analysis_table}
"""

    thoughts = openai_client.responses.create(
        model="gpt-5",
        instruction=roi_prompt,
        input=input_text,
        reasoning={"effort": "medium"},
        temperature=0.2,
        truncation="auto"
    )

    return thoughts.output_text