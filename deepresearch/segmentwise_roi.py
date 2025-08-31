from utils.openai_client import openai_client, litellm_client
from datastore.models import Product, CustomerSegment, ProductPricingModel, CustomerUsageAnalysis, PricingPlanSegmentContribution
from .prompts import roi_prompt
from bson.objectid import ObjectId
import random
from datetime import datetime, timedelta


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


def sample_user_tasks(usage_analyses, sample_size=10):
    """Sample user tasks for analysis, prioritizing diverse and high-value tasks"""
    if not usage_analyses:
        return []

    # Convert to list if it's a queryset
    usage_list = list(usage_analyses)

    # Sample tasks, preferring those with satisfaction scores and diverse segments
    sampled_tasks = []

    # First, get tasks with satisfaction scores
    scored_tasks = [task for task in usage_list if task.predicted_customer_satisfaction_response is not None]
    unscored_tasks = [task for task in usage_list if task.predicted_customer_satisfaction_response is None]

    # Sample from scored tasks first (up to 70% of sample)
    scored_sample_size = min(len(scored_tasks), int(sample_size * 0.7))
    if scored_sample_size > 0:
        sampled_tasks.extend(random.sample(scored_tasks, scored_sample_size))

    # Fill remaining with unscored tasks
    remaining_slots = sample_size - len(sampled_tasks)
    if remaining_slots > 0 and unscored_tasks:
        unscored_sample_size = min(len(unscored_tasks), remaining_slots)
        sampled_tasks.extend(random.sample(unscored_tasks, unscored_sample_size))

    return sampled_tasks


def get_segment_cost_revenue_data(product_id):
    """Get cost and revenue data for each segment"""
    contributions = PricingPlanSegmentContribution.objects(product=ObjectId(product_id)).all()

    segment_data = {}

    for contribution in contributions:
        segment_uid = contribution.customer_segment.customer_segment_uid
        segment_name = contribution.customer_segment.customer_segment_name

        if segment_uid not in segment_data:
            segment_data[segment_uid] = {
                'segment_name': segment_name,
                'total_revenue': 0,
                'total_subscriptions': 0,
                'revenue_history': [],
                'subscription_history': [],
                'pricing_plan': contribution.pricing_plan,
                'unit_price': contribution.pricing_plan.unit_price if contribution.pricing_plan else 0,
                'min_unit_count': contribution.pricing_plan.min_unit_count if contribution.pricing_plan else 0
            }

        # Aggregate revenue data
        for revenue_point in contribution.revenue_ts_data:
            segment_data[segment_uid]['total_revenue'] += revenue_point.value
            segment_data[segment_uid]['revenue_history'].append({
                'date': revenue_point.date,
                'value': revenue_point.value
            })

        # Aggregate subscription data
        for sub_point in contribution.active_subscriptions:
            segment_data[segment_uid]['total_subscriptions'] += sub_point.value
            segment_data[segment_uid]['subscription_history'].append({
                'date': sub_point.date,
                'value': sub_point.value
            })

    return segment_data


def format_cost_revenue_table(segment_data):
    """Format segment cost/revenue data into a readable table"""
    if not segment_data:
        return "No cost/revenue data available."

    table = "| Segment | Total Revenue | Subscriptions | Avg Revenue/User | Unit Price | Min Units |\n"
    table += "|---------|---------------|---------------|-----------------|------------|-----------|\n"

    for segment_uid, data in segment_data.items():
        segment_name = data['segment_name'] or "N/A"
        total_revenue = data['total_revenue']
        total_subs = data['total_subscriptions']
        avg_revenue = total_revenue / total_subs if total_subs > 0 else 0
        unit_price = data['unit_price']
        min_units = data['min_unit_count']

        table += f"| {segment_name} | ${total_revenue:,.2f} | {int(total_subs)} | ${avg_revenue:,.2f} | ${unit_price:,.2f} | {min_units} |\n"

    return table


def agent(product_id, product_research):
    # Get all required data
    all_segments = CustomerSegment.objects(product=ObjectId(product_id)).all()
    all_usage_analysis = CustomerUsageAnalysis.objects(product=ObjectId(product_id)).all()

    # Get cost and revenue data
    segment_cost_revenue = get_segment_cost_revenue_data(product_id)

    # Sample user tasks for detailed analysis
    sampled_tasks = sample_user_tasks(all_usage_analysis, sample_size=15)

    # Format tables
    segments_table = format_segments_table(all_segments)
    full_usage_table = format_usage_analysis_table(all_usage_analysis)
    sampled_usage_table = format_usage_analysis_table(sampled_tasks)
    cost_revenue_table = format_cost_revenue_table(segment_cost_revenue)

    input_text = f"""
## Product Research Context
{product_research}

---
## Customer Segments Overview
{segments_table}

---
## Cost & Revenue Analysis by Segment
{cost_revenue_table}

---
## Sampled User Tasks Analysis (15 representative tasks)
{sampled_usage_table}

---
## Complete Usage Analysis Data
{full_usage_table}
"""

    thoughts = openai_client.responses.create(
        model="gpt-5",
        instruction=roi_prompt,
        input=input_text,
        reasoning={"effort": "high"},
        temperature=0.1,
        truncation="auto",
        tools=[
            {"type": "code_interpreter", "container": {"type": "auto"}}
        ],
        tool_choice="auto",
        max_tool_calls=10
    )

    return thoughts.output_text