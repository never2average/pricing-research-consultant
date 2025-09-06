import random
import logging
import traceback
from typing import List, Optional, Any
from .prompts import roi_prompt
from bson.objectid import ObjectId
from utils.openai_client import openai_client
from datastore.models import CustomerSegment, CustomerUsageAnalysis, PricingPlanSegmentContribution

logger = logging.getLogger(__name__)


def format_segments_table(segments: List[Any]) -> str:
    try:
        if not segments:
            return "No customer segments found."
        
        table = "| Segment UID | Segment Name | Description |\n"
        table += "|-------------|--------------|-------------|\n"
        
        for segment in segments:
            try:
                uid = segment.customer_segment_uid or "N/A"
                name = segment.customer_segment_name or "N/A"
                description = segment.customer_segment_description or "N/A"
                table += f"| {uid} | {name} | {description} |\n"
            except AttributeError as e:
                logger.error(f"Error accessing segment attributes: {e}")
                logger.error(f"Full stack trace: {traceback.format_exc()}")
                table += "| Error | Error | Error accessing segment data |\n"
            except Exception as e:
                logger.error(f"Unexpected error formatting segment row: {e}")
                logger.error(f"Full stack trace: {traceback.format_exc()}")
                table += "| Error | Error | Unexpected error |\n"
        
        return table
    except Exception as e:
        logger.error(f"Error formatting segments table: {e}")
        logger.error(f"Full stack trace: {traceback.format_exc()}")
        return "Error: Could not format segments table"


def format_usage_analysis_table(usage_analyses):
    try:
        if not usage_analyses:
            return "No usage analyses found."

        table = "| Customer UID | Segment | Task Description | Satisfaction Score | Reasoning |\n"
        table += "|--------------|---------|------------------|-------------------|----------|\n"

        for analysis in usage_analyses:
            try:
                customer_uid = analysis.customer_uid or "N/A"
                
                # Safely access nested customer_segment
                try:
                    segment_name = analysis.customer_segment.customer_segment_name if analysis.customer_segment else "N/A"
                except AttributeError:
                    segment_name = "N/A"
                
                task = analysis.customer_task_to_agent or "N/A"
                satisfaction = analysis.predicted_customer_satisfaction_response or "N/A"
                reasoning = analysis.predicted_customer_satisfaction_response_reasoning or "N/A"

                # Truncate long text for table readability
                try:
                    task = task[:50] + "..." if len(task) > 50 else task
                    reasoning = reasoning[:100] + "..." if len(reasoning) > 100 else reasoning
                except (TypeError, AttributeError):
                    task = str(task)[:50] + "..." if len(str(task)) > 50 else str(task)
                    reasoning = str(reasoning)[:100] + "..." if len(str(reasoning)) > 100 else str(reasoning)

                table += f"| {customer_uid} | {segment_name} | {task} | {satisfaction} | {reasoning} |\n"
                
            except AttributeError as e:
                logger.error(f"Error accessing usage analysis attributes: {e}")
                logger.error(f"Full stack trace: {traceback.format_exc()}")
                table += "| Error | Error | Error accessing analysis data | Error | Error |\n"
            except Exception as e:
                logger.error(f"Unexpected error formatting usage analysis row: {e}")
                logger.error(f"Full stack trace: {traceback.format_exc()}")
                table += "| Error | Error | Unexpected error | Error | Error |\n"

        return table
    except Exception as e:
        logger.error(f"Error formatting usage analysis table: {e}")
        logger.error(f"Full stack trace: {traceback.format_exc()}")
        return "Error: Could not format usage analysis table"


def sample_user_tasks(usage_analyses, sample_size=10):
    """Sample user tasks for analysis, prioritizing diverse and high-value tasks"""
    try:
        if not usage_analyses:
            return []

        # Convert to list if it's a queryset
        try:
            usage_list = list(usage_analyses)
        except Exception as e:
            logger.error(f"Error converting usage_analyses to list: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return []

        # Sample tasks, preferring those with satisfaction scores and diverse segments
        sampled_tasks = []

        try:
            # First, get tasks with satisfaction scores
            scored_tasks = []
            unscored_tasks = []
            
            for task in usage_list:
                try:
                    if hasattr(task, 'predicted_customer_satisfaction_response') and task.predicted_customer_satisfaction_response is not None:
                        scored_tasks.append(task)
                    else:
                        unscored_tasks.append(task)
                except Exception as e:
                    logger.error(f"Error checking task satisfaction response: {e}")
                    logger.error(f"Full stack trace: {traceback.format_exc()}")
                    unscored_tasks.append(task)

            # Sample from scored tasks first (up to 70% of sample)
            try:
                scored_sample_size = min(len(scored_tasks), int(sample_size * 0.7))
                if scored_sample_size > 0:
                    sampled_tasks.extend(random.sample(scored_tasks, scored_sample_size))
            except ValueError as e:
                logger.error(f"Error sampling scored tasks: {e}")
                logger.error(f"Full stack trace: {traceback.format_exc()}")
            except Exception as e:
                logger.error(f"Unexpected error sampling scored tasks: {e}")
                logger.error(f"Full stack trace: {traceback.format_exc()}")

            # Fill remaining with unscored tasks
            try:
                remaining_slots = sample_size - len(sampled_tasks)
                if remaining_slots > 0 and unscored_tasks:
                    unscored_sample_size = min(len(unscored_tasks), remaining_slots)
                    sampled_tasks.extend(random.sample(unscored_tasks, unscored_sample_size))
            except ValueError as e:
                logger.error(f"Error sampling unscored tasks: {e}")
                logger.error(f"Full stack trace: {traceback.format_exc()}")
            except Exception as e:
                logger.error(f"Unexpected error sampling unscored tasks: {e}")
                logger.error(f"Full stack trace: {traceback.format_exc()}")

        except Exception as e:
            logger.error(f"Error during task sampling process: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            # Return first N tasks as fallback
            try:
                return usage_list[:sample_size]
            except:
                return []

        return sampled_tasks
        
    except Exception as e:
        logger.error(f"Error in sample_user_tasks: {e}")
        logger.error(f"Full stack trace: {traceback.format_exc()}")
        return []


def get_segment_cost_revenue_data(product_id):
    """Get cost and revenue data for each segment"""
    try:
        # Validate and convert product_id to ObjectId
        try:
            product_obj_id = ObjectId(product_id)
        except Exception as e:
            logger.error(f"Invalid product_id format: {product_id}, error: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return {}

        try:
            contributions = PricingPlanSegmentContribution.objects(product=product_obj_id).all()
        except Exception as e:
            logger.error(f"Error querying PricingPlanSegmentContribution for product {product_id}: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return {}

        segment_data = {}

        for contribution in contributions:
            try:
                # Safely access segment data
                try:
                    segment_uid = contribution.customer_segment.customer_segment_uid
                    segment_name = contribution.customer_segment.customer_segment_name
                except AttributeError as e:
                    logger.error(f"Error accessing customer segment data: {e}")
                    logger.error(f"Full stack trace: {traceback.format_exc()}")
                    continue

                if segment_uid not in segment_data:
                    try:
                        unit_price = contribution.pricing_plan.unit_price if contribution.pricing_plan else 0
                        min_unit_count = contribution.pricing_plan.min_unit_count if contribution.pricing_plan else 0
                    except AttributeError as e:
                        logger.error(f"Error accessing pricing plan data: {e}")
                        logger.error(f"Full stack trace: {traceback.format_exc()}")
                        unit_price = 0
                        min_unit_count = 0
                    
                    segment_data[segment_uid] = {
                        'segment_name': segment_name,
                        'total_revenue': 0,
                        'total_subscriptions': 0,
                        'revenue_history': [],
                        'subscription_history': [],
                        'pricing_plan': contribution.pricing_plan,
                        'unit_price': unit_price,
                        'min_unit_count': min_unit_count
                    }

                # Aggregate revenue data
                try:
                    for revenue_point in contribution.revenue_ts_data or []:
                        try:
                            segment_data[segment_uid]['total_revenue'] += revenue_point.value
                            segment_data[segment_uid]['revenue_history'].append({
                                'date': revenue_point.date,
                                'value': revenue_point.value
                            })
                        except (AttributeError, TypeError) as e:
                            logger.error(f"Error processing revenue point: {e}")
                            logger.error(f"Full stack trace: {traceback.format_exc()}")
                            continue
                except Exception as e:
                    logger.error(f"Error processing revenue data: {e}")
                    logger.error(f"Full stack trace: {traceback.format_exc()}")

                # Aggregate subscription data
                try:
                    for sub_point in contribution.active_subscriptions or []:
                        try:
                            segment_data[segment_uid]['total_subscriptions'] += sub_point.value
                            segment_data[segment_uid]['subscription_history'].append({
                                'date': sub_point.date,
                                'value': sub_point.value
                            })
                        except (AttributeError, TypeError) as e:
                            logger.error(f"Error processing subscription point: {e}")
                            logger.error(f"Full stack trace: {traceback.format_exc()}")
                            continue
                except Exception as e:
                    logger.error(f"Error processing subscription data: {e}")
                    logger.error(f"Full stack trace: {traceback.format_exc()}")

            except Exception as e:
                logger.error(f"Error processing contribution record: {e}")
                logger.error(f"Full stack trace: {traceback.format_exc()}")
                continue

        return segment_data
        
    except Exception as e:
        logger.error(f"Error in get_segment_cost_revenue_data: {e}")
        logger.error(f"Full stack trace: {traceback.format_exc()}")
        return {}


def format_cost_revenue_table(segment_data):
    """Format segment cost/revenue data into a readable table"""
    try:
        if not segment_data:
            return "No cost/revenue data available."

        table = "| Segment | Plan | Total Revenue | Subscriptions | Avg Revenue/User | Unit Price | Min Units |\n"
        table += "|---------|------|---------------|---------------|-----------------|------------|-----------|\n"

        for segment_uid, data in segment_data.items():
            try:
                segment_name = data.get('segment_name', "N/A") or "N/A"
                
                # Safely access plan name
                try:
                    plan_name = data['pricing_plan'].plan_name if data.get('pricing_plan') and hasattr(data['pricing_plan'], 'plan_name') and data['pricing_plan'].plan_name else "N/A"
                except (AttributeError, TypeError):
                    plan_name = "N/A"
                
                total_revenue = data.get('total_revenue', 0)
                total_subs = data.get('total_subscriptions', 0)
                
                # Calculate average revenue safely
                try:
                    avg_revenue = total_revenue / total_subs if total_subs > 0 else 0
                except (TypeError, ZeroDivisionError):
                    avg_revenue = 0
                
                unit_price = data.get('unit_price', 0)
                min_units = data.get('min_unit_count', 0)

                # Format numbers safely
                try:
                    table += f"| {segment_name} | {plan_name} | ${total_revenue:,.2f} | {int(total_subs)} | ${avg_revenue:,.2f} | ${unit_price:,.2f} | {min_units} |\n"
                except (ValueError, TypeError) as e:
                    logger.error(f"Error formatting table row for segment {segment_uid}: {e}")
                    logger.error(f"Full stack trace: {traceback.format_exc()}")
                    table += f"| {segment_name} | {plan_name} | Error | Error | Error | Error | Error |\n"
                    
            except Exception as e:
                logger.error(f"Error processing segment {segment_uid}: {e}")
                logger.error(f"Full stack trace: {traceback.format_exc()}")
                table += "| Error | Error | Error | Error | Error | Error | Error |\n"

        return table
    except Exception as e:
        logger.error(f"Error in format_cost_revenue_table: {e}")
        logger.error(f"Full stack trace: {traceback.format_exc()}")
        return "Error: Could not format cost/revenue table"


def agent(product_id: str, product_research: str, pricing_objective: Optional[str] = None) -> str:
    try:
        logger.info(f"Starting segmentwise ROI analysis for product {product_id}")
        
        # Validate inputs
        if not product_id:
            logger.error("product_id is required")
            return "Error: Product ID is required"
        
        if not product_research:
            logger.warning("product_research is empty, proceeding with analysis")
        
        # Get all required data with error handling
        try:
            product_obj_id = ObjectId(product_id)
            all_segments = CustomerSegment.objects(product=product_obj_id).all()
            logger.info(f"Retrieved {len(all_segments)} customer segments")
        except Exception as e:
            logger.error(f"Error fetching customer segments for product {product_id}: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return "Error: Could not fetch customer segments"

        try:
            all_usage_analysis = CustomerUsageAnalysis.objects(product=product_obj_id).all()
            logger.info(f"Retrieved {len(all_usage_analysis)} usage analyses")
        except Exception as e:
            logger.error(f"Error fetching usage analysis for product {product_id}: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return "Error: Could not fetch usage analysis data"

        # Get cost and revenue data
        try:
            segment_cost_revenue = get_segment_cost_revenue_data(product_id)
            logger.info(f"Retrieved cost/revenue data for {len(segment_cost_revenue)} segments")
        except Exception as e:
            logger.error(f"Error getting cost/revenue data: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            segment_cost_revenue = {}

        # Sample user tasks for detailed analysis
        try:
            sampled_tasks = sample_user_tasks(all_usage_analysis, sample_size=15)
            logger.info(f"Sampled {len(sampled_tasks)} tasks for analysis")
        except Exception as e:
            logger.error(f"Error sampling user tasks: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            sampled_tasks = []

        # Format tables with error handling
        try:
            segments_table = format_segments_table(all_segments)
        except Exception as e:
            logger.error(f"Error formatting segments table: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            segments_table = "Error: Could not format segments table"

        try:
            full_usage_table = format_usage_analysis_table(all_usage_analysis)
        except Exception as e:
            logger.error(f"Error formatting full usage table: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            full_usage_table = "Error: Could not format usage analysis table"

        try:
            sampled_usage_table = format_usage_analysis_table(sampled_tasks)
        except Exception as e:
            logger.error(f"Error formatting sampled usage table: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            sampled_usage_table = "Error: Could not format sampled usage table"

        try:
            cost_revenue_table = format_cost_revenue_table(segment_cost_revenue)
        except Exception as e:
            logger.error(f"Error formatting cost/revenue table: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            cost_revenue_table = "Error: Could not format cost/revenue table"

        # Prepare input text
        try:
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
            
            if pricing_objective:
                input_text = f"{input_text}\n\n---\n## Pricing Objective\n{pricing_objective}"
        except Exception as e:
            logger.error(f"Error preparing input text: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return "Error: Could not prepare analysis input"

        # Call OpenAI API with error handling
        try:
            thoughts = openai_client.responses.create(
                model="gpt-5",
                instructions=roi_prompt,
                input=input_text,
                reasoning={"effort": "high"},
                truncation="auto",
                tools=[
                    {"type": "code_interpreter", "container": {"type": "auto"}}
                ],
                tool_choice="auto",
                max_tool_calls=10
            )
            
            logger.info("Successfully completed OpenAI analysis")
            return thoughts.output_text
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return "Error: Could not complete AI analysis. Please try again later."

    except Exception as e:
        logger.error(f"Unexpected error in segmentwise ROI agent: {e}")
        logger.error(f"Full stack trace: {traceback.format_exc()}")
        return "Error: An unexpected error occurred during analysis"