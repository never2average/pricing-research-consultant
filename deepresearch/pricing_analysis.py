import logging
import traceback
from bson import ObjectId
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from utils.openai_client import openai_client, litellm_client
from datastore.models import Product, CustomerSegment, ProductPricingModel
from datastore.models import PricingPlanSegmentContribution, TimeseriesData
from datastore.connectors import create_pricing_plan_segment_contribution
from .prompts import pricing_analysis_system_prompt, structured_parsing_system_prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('pricing_analysis.log')  # File output
    ]
)

logger = logging.getLogger(__name__)


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
    forecasts: List[SegmentPlanForecast]

def save_pricing_forecasts(product_id: str, parsed_response: PricingAnalysisResponse):
    """Save the parsed forecast data to PricingPlanSegmentContribution records"""
    try:
        logger.info(f"Starting to save pricing forecasts for product {product_id}")
        
        # Validate inputs
        if not product_id:
            logger.error("product_id is required")
            return
        
        if not parsed_response:
            logger.error("parsed_response is missing or None")
            return
            
        if not hasattr(parsed_response, 'forecasts'):
            logger.error("parsed_response does not have forecasts attribute")
            return
            
        if not parsed_response.forecasts:
            logger.warning("parsed_response.forecasts is empty - no forecast data to save")
            return
        
        # Validate product_id format
        try:
            product_obj_id = ObjectId(product_id)
        except Exception as e:
            logger.error(f"Invalid product_id format: {product_id}, error: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return
        
        for i, forecast in enumerate(parsed_response.forecasts):
            try:
                logger.info(f"Processing forecast {i+1}/{len(parsed_response.forecasts)}")
                
                # Find the matching PricingPlanSegmentContribution record
                filters = {"product": product_obj_id}
                
                if forecast.customer_segment_uid:
                    try:
                        segment = CustomerSegment.objects(
                            product=product_obj_id,
                            customer_segment_uid=forecast.customer_segment_uid
                        ).first()
                        if segment:
                            filters["customer_segment"] = segment
                        else:
                            logger.info(f"No segment found for UID: {forecast.customer_segment_uid}, creating new segment")
                            # Create new customer segment
                            try:
                                new_segment = CustomerSegment(
                                    product=product_obj_id,
                                    customer_segment_uid=forecast.customer_segment_uid,
                                    customer_segment_name=f"Segment {forecast.customer_segment_uid}",
                                    customer_segment_description=f"Auto-generated segment for UID: {forecast.customer_segment_uid}"
                                )
                                new_segment.save()
                                filters["customer_segment"] = new_segment
                                logger.info(f"Successfully created new customer segment: {forecast.customer_segment_uid}")
                            except Exception as create_error:
                                logger.error(f"Error creating new customer segment: {create_error}")
                                logger.error(f"Full stack trace: {traceback.format_exc()}")
                    except Exception as e:
                        logger.error(f"Error finding customer segment: {e}")
                        logger.error(f"Full stack trace: {traceback.format_exc()}")
                
                if forecast.pricing_plan_id:
                    try:
                        filters["pricing_plan"] = ObjectId(forecast.pricing_plan_id)
                    except Exception as e:
                        logger.error(f"Invalid pricing_plan_id format: {forecast.pricing_plan_id}, error: {e}")
                        logger.error(f"Full stack trace: {traceback.format_exc()}")
                
                # Find existing record
                try:
                    existing_record = PricingPlanSegmentContribution.objects(**filters).first()
                except Exception as e:
                    logger.error(f"Error querying PricingPlanSegmentContribution: {e}")
                    logger.error(f"Full stack trace: {traceback.format_exc()}")
                    continue
                
                if existing_record:
                    logger.info(f"Found existing record, updating forecasts")
                    
                    # Convert revenue forecast data
                    if forecast.revenue_forecast_ts_data:
                        try:
                            revenue_ts_data = []
                            for j, point in enumerate(forecast.revenue_forecast_ts_data):
                                try:
                                    # Try ISO format first
                                    try:
                                        date_obj = datetime.fromisoformat(point.date.replace('Z', '+00:00'))
                                    except (ValueError, AttributeError):
                                        # Fallback to simple date format
                                        date_obj = datetime.strptime(point.date, '%Y-%m-%d')
                                    
                                    revenue_ts_data.append(TimeseriesData(
                                        date=date_obj,
                                        value=point.revenue
                                    ))
                                except Exception as e:
                                    logger.error(f"Error processing revenue point {j}: {e}")
                                    logger.error(f"Full stack trace: {traceback.format_exc()}")
                                    continue
                            
                            existing_record.revenue_forecast_ts_data = revenue_ts_data
                            logger.info(f"Updated {len(revenue_ts_data)} revenue forecast points")
                            
                        except Exception as e:
                            logger.error(f"Error processing revenue forecast data: {e}")
                            logger.error(f"Full stack trace: {traceback.format_exc()}")
                    
                    # Convert subscription forecast data
                    if forecast.active_subscriptions_forecast:
                        try:
                            subscriptions_ts_data = []
                            for j, point in enumerate(forecast.active_subscriptions_forecast):
                                try:
                                    # Try ISO format first
                                    try:
                                        date_obj = datetime.fromisoformat(point.date.replace('Z', '+00:00'))
                                    except (ValueError, AttributeError):
                                        # Fallback to simple date format
                                        date_obj = datetime.strptime(point.date, '%Y-%m-%d')
                                    
                                    subscriptions_ts_data.append(TimeseriesData(
                                        date=date_obj,
                                        value=point.revenue
                                    ))
                                except Exception as e:
                                    logger.error(f"Error processing subscription point {j}: {e}")
                                    logger.error(f"Full stack trace: {traceback.format_exc()}")
                                    continue
                            
                            existing_record.active_subscriptions_forecast = subscriptions_ts_data
                            logger.info(f"Updated {len(subscriptions_ts_data)} subscription forecast points")
                            
                        except Exception as e:
                            logger.error(f"Error processing subscription forecast data: {e}")
                            logger.error(f"Full stack trace: {traceback.format_exc()}")
                    
                    # Save the updated record
                    try:
                        existing_record.save()
                        logger.info(f"Successfully saved forecast data for record {i+1}")
                    except Exception as e:
                        logger.error(f"Error saving record: {e}")
                        logger.error(f"Full stack trace: {traceback.format_exc()}")
                        
                else:
                    logger.warning(f"No existing PricingPlanSegmentContribution record found for forecast {i+1}")
                    # Create new PricingPlanSegmentContribution record
                    try:
                        logger.info(f"Creating new PricingPlanSegmentContribution record for forecast {i+1}")
                        
                        # Find customer segment
                        segment = None
                        if forecast.customer_segment_uid:
                            try:
                                segment = CustomerSegment.objects(
                                    product=product_obj_id,
                                    customer_segment_uid=forecast.customer_segment_uid
                                ).first()
                                if not segment:
                                    logger.info(f"Creating new customer segment for UID: {forecast.customer_segment_uid}")
                                    segment = CustomerSegment(
                                        product=product_obj_id,
                                        customer_segment_uid=forecast.customer_segment_uid,
                                        customer_segment_name=f"Segment {forecast.customer_segment_uid}",
                                        customer_segment_description=f"Auto-generated segment for UID: {forecast.customer_segment_uid}"
                                    )
                                    segment.save()
                            except Exception as e:
                                logger.error(f"Error finding/creating customer segment: {e}")
                        
                        # Find pricing plan
                        pricing_plan = None
                        if forecast.pricing_plan_id:
                            try:
                                pricing_plan = ProductPricingModel.objects(id=ObjectId(forecast.pricing_plan_id)).first()
                            except Exception as e:
                                logger.error(f"Error finding pricing plan: {e}")
                        
                        # If we have both segment and pricing plan, create the record
                        if segment and pricing_plan:
                            new_record = create_pricing_plan_segment_contribution(
                                Product.objects(id=product_obj_id).first(), segment, pricing_plan
                            )
                            logger.info(f"Created new PricingPlanSegmentContribution record: {new_record.id}")
                            
                            # Now save forecast data to the new record
                            # Convert revenue forecast data
                            if forecast.revenue_forecast_ts_data:
                                try:
                                    revenue_ts_data = []
                                    for j, point in enumerate(forecast.revenue_forecast_ts_data):
                                        try:
                                            # Try ISO format first
                                            try:
                                                date_obj = datetime.fromisoformat(point.date.replace('Z', '+00:00'))
                                            except (ValueError, AttributeError):
                                                # Fallback to simple date format
                                                date_obj = datetime.strptime(point.date, '%Y-%m-%d')
                                            
                                            revenue_ts_data.append(TimeseriesData(
                                                date=date_obj,
                                                value=point.revenue
                                            ))
                                        except Exception as e:
                                            logger.error(f"Error processing revenue point {j}: {e}")
                                            continue
                                    
                                    new_record.revenue_forecast_ts_data = revenue_ts_data
                                    logger.info(f"Updated {len(revenue_ts_data)} revenue forecast points")
                                    
                                except Exception as e:
                                    logger.error(f"Error processing revenue forecast data: {e}")
                            
                            # Convert subscription forecast data
                            if forecast.active_subscriptions_forecast:
                                try:
                                    subscriptions_ts_data = []
                                    for j, point in enumerate(forecast.active_subscriptions_forecast):
                                        try:
                                            # Try ISO format first
                                            try:
                                                date_obj = datetime.fromisoformat(point.date.replace('Z', '+00:00'))
                                            except (ValueError, AttributeError):
                                                # Fallback to simple date format
                                                date_obj = datetime.strptime(point.date, '%Y-%m-%d')
                                            
                                            subscriptions_ts_data.append(TimeseriesData(
                                                date=date_obj,
                                                value=point.revenue
                                            ))
                                        except Exception as e:
                                            logger.error(f"Error processing subscription point {j}: {e}")
                                            continue
                                    
                                    new_record.active_subscriptions_forecast = subscriptions_ts_data
                                    logger.info(f"Updated {len(subscriptions_ts_data)} subscription forecast points")
                                    
                                except Exception as e:
                                    logger.error(f"Error processing subscription forecast data: {e}")
                            
                            # Save the new record
                            try:
                                new_record.save()
                                logger.info(f"Successfully saved forecast data for new record {i+1}")
                            except Exception as e:
                                logger.error(f"Error saving new record: {e}")
                                logger.error(f"Full stack trace: {traceback.format_exc()}")
                            
                        else:
                            logger.error(f"Cannot create record - missing segment ({segment is not None}) or pricing plan ({pricing_plan is not None}) for forecast {i+1}")
                            
                    except Exception as create_error:
                        logger.error(f"Error creating new PricingPlanSegmentContribution record: {create_error}")
                        logger.error(f"Full stack trace: {traceback.format_exc()}")
                    
            except Exception as e:
                logger.error(f"Error processing forecast {i+1}: {e}")
                logger.error(f"Full stack trace: {traceback.format_exc()}")
                continue
        
        logger.info("Completed saving pricing forecasts")
        
    except Exception as e:
        logger.error(f"Error in save_pricing_forecasts: {e}")
        logger.error(f"Full stack trace: {traceback.format_exc()}")
        return

def agent(product_id: str, segment_ids: List[str]=None):
    try:
        logger.info(f"Starting pricing analysis for product {product_id}")
        
        # Validate inputs
        if not product_id:
            logger.error("product_id is required")
            return "Error: Product ID is required"
        
        # Validate and convert product_id to ObjectId
        try:
            product_obj_id = ObjectId(product_id)
        except Exception as e:
            logger.error(f"Invalid product_id format: {product_id}, error: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return "Error: Invalid product ID format"

        # Get product data
        try:
            product = Product.objects(id=product_obj_id).first()
            if not product:
                logger.error(f"Product not found with ID: {product_id}")
                return "Error: Product not found"
            logger.info(f"Retrieved product: {product.name}")
        except Exception as e:
            logger.error(f"Error fetching product: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return "Error: Could not fetch product data"

        # Get customer segments with error handling
        try:
            if segment_ids:
                try:
                    # Validate segment_ids format
                    segment_obj_ids = []
                    for seg_id in segment_ids:
                        try:
                            segment_obj_ids.append(ObjectId(seg_id))
                        except Exception as e:
                            logger.warning(f"Invalid segment_id format: {seg_id}, skipping")
                    
                    all_segments = CustomerSegment.objects(
                        product=product_obj_id,
                        id__in=segment_obj_ids
                    ).all()
                except Exception as e:
                    logger.error(f"Error processing segment_ids: {e}")
                    logger.error(f"Full stack trace: {traceback.format_exc()}")
                    # Fallback to all segments
                    all_segments = CustomerSegment.objects(product=product_obj_id).all()
            else:
                all_segments = CustomerSegment.objects(product=product_obj_id).all()
            
            logger.info(f"Retrieved {len(all_segments)} customer segments")
        except Exception as e:
            logger.error(f"Error fetching customer segments: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return "Error: Could not fetch customer segments"
            
        # Get pricing plan contributions
        try:
            all_segment_pricing_plans = PricingPlanSegmentContribution.objects(
                product=product_obj_id,
                customer_segment__in=all_segments
            ).all()
            logger.info(f"Retrieved {len(all_segment_pricing_plans)} pricing plan contributions")
        except Exception as e:
            logger.error(f"Error fetching pricing plan contributions: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return "Error: Could not fetch pricing plan data"

        # Build markdown table for segmentwise usage/revenue
        try:
            table_rows = ["| Segment | Plan | Current Revenue | Current Subscriptions | Forecast Revenue | Forecast Subscriptions |"]
            table_rows.append("|---------|------|-----------------|----------------------|------------------|------------------------|")

            for plan_contribution in all_segment_pricing_plans:
                try:
                    # Safely access segment name
                    try:
                        segment_name = plan_contribution.customer_segment.customer_segment_name or "N/A"
                    except AttributeError:
                        segment_name = "N/A"
                    
                    # Safely access plan name
                    try:
                        plan_name = (plan_contribution.pricing_plan.plan_name or 
                                   plan_contribution.pricing_plan.unit_calculation_logic or 
                                   f"Plan {str(plan_contribution.pricing_plan.id)}")
                    except AttributeError:
                        plan_name = "N/A"

                    # Get latest revenue and subscriptions data safely
                    try:
                        current_revenue = plan_contribution.revenue_ts_data[-1].value if plan_contribution.revenue_ts_data else 0
                    except (IndexError, AttributeError):
                        current_revenue = 0
                    
                    try:
                        current_subs = plan_contribution.active_subscriptions[-1].value if plan_contribution.active_subscriptions else 0
                    except (IndexError, AttributeError):
                        current_subs = 0

                    # Get latest forecast data safely
                    try:
                        forecast_revenue = plan_contribution.revenue_forecast_ts_data[-1].value if plan_contribution.revenue_forecast_ts_data else 0
                    except (IndexError, AttributeError):
                        forecast_revenue = 0
                    
                    try:
                        forecast_subs = plan_contribution.active_subscriptions_forecast[-1].value if plan_contribution.active_subscriptions_forecast else 0
                    except (IndexError, AttributeError):
                        forecast_subs = 0

                    table_rows.append(f"| {segment_name} | {plan_name} | ${current_revenue:,.0f} | {current_subs:,.0f} | ${forecast_revenue:,.0f} | {forecast_subs:,.0f} |")
                    
                except Exception as e:
                    logger.error(f"Error processing plan contribution: {e}")
                    logger.error(f"Full stack trace: {traceback.format_exc()}")
                    table_rows.append("| Error | Error | Error | Error | Error | Error |")

            table_content = "\n".join(table_rows)
            logger.info("Successfully built pricing table")
            
        except Exception as e:
            logger.error(f"Error building pricing table: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            table_content = "Error: Could not generate pricing table"

        # Prepare prompt
        try:
            prompt = f"""
## Product Name:
{getattr(product, 'name', 'Unknown')}

## Product Description:
{getattr(product, 'features_description_summary', 'No description available')}

## Pricing Content:
{table_content}
"""
        except Exception as e:
            logger.error(f"Error preparing prompt: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return "Error: Could not prepare analysis prompt"
        
        # Call OpenAI API
        try:
            tools = [
                {"type": "web_search_preview"},
                {
                    "type": "code_interpreter",
                    "container": {"type": "auto"}
                }
            ]
            
            # Add file_search tool if vector store exists
            try:
                if hasattr(product, 'vector_store_id') and product.vector_store_id:
                    tools.append({
                        "type": "file_search",
                        "vector_store_ids": [product.vector_store_id]
                    })
            except Exception as e:
                logger.warning(f"Could not add file_search tool: {e}")
            
            draft = openai_client.responses.create(
                model="gpt-5",
                reasoning={"effort": "low"},
                truncation="auto",
                tool_choice="auto",
                max_tool_calls=10,
                tools=tools,
                input=[
                    {"role": "system", "content": pricing_analysis_system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            logger.info("Successfully completed OpenAI pricing analysis")
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            return "Error: Could not complete AI analysis. Please try again later."

        # Parse the response with LiteLLM
        try:
            parsed = litellm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": structured_parsing_system_prompt},
                    {"role": "user", "content": draft.output_text}
                ],
                response_model=PricingAnalysisResponse
            )
            logger.info("Successfully parsed response with LiteLLM")
            logger.info(f"Parsed response type: {type(parsed)}")
            logger.info(f"Parsed response has forecasts: {hasattr(parsed, 'forecasts')}")
            if hasattr(parsed, 'forecasts'):
                logger.info(f"Number of forecasts: {len(parsed.forecasts) if parsed.forecasts else 0}")
                if parsed.forecasts:
                    for i, forecast in enumerate(parsed.forecasts):
                        logger.info(f"Forecast {i}: segment_uid={forecast.customer_segment_uid}, plan_id={forecast.pricing_plan_id}")
            else:
                logger.warning("Parsed response does not have forecasts attribute")
        except Exception as e:
            logger.error(f"Error parsing response with LiteLLM: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            logger.error(f"Draft output text sample (first 500 chars): {draft.output_text[:500]}")
            # Return the draft without parsing
            return draft.output_text

        # Save pricing forecasts
        try:
            save_pricing_forecasts(product_id, parsed)
        except Exception as e:
            logger.error(f"Error saving pricing forecasts: {e}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")
            # Continue and return the analysis even if save fails

        return draft.output_text
        
    except Exception as e:
        logger.error(f"Unexpected error in pricing analysis agent: {e}")
        logger.error(f"Full stack trace: {traceback.format_exc()}")
        return "Error: An unexpected error occurred during analysis"