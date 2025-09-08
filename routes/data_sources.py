from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel
from deepresearch_nonfunctional.llms_txt_builder_agent import generate_llms_integrator_primer
from logical_functions.github_lambda_deployer import deploy_github_repo_to_lambda, get_deployment_status
from logical_functions.email_service import send_enterprise_sow_email
from logical_functions.orb_deployment import deploy_pricing_to_orb
from logical_functions.golive_data_manager import (
    save_golive_action_to_product,
    get_product_golive_actions,
    validate_product_exists
)

router = APIRouter()


class ToolConfigRequest(BaseModel):
    product_tool: str
    customer_tool: str
    revenue_tool: str


class GitHubDeploymentRequest(BaseModel):
    github_url: str


class DeploymentStatusRequest(BaseModel):
    function_name: str


class PricingData(BaseModel):
    pricing_name: str
    pricing_tiers: List[Dict[str, str]]
    pricing_model: str
    effective_date: str
    customer_segments: List[str]


class GoLiveActionRequest(BaseModel):
    product_id: str  # MongoDB Product document ID
    action_type: str  # "email_sow" or "deploy_orb"
    pricing_data: PricingData
    customer_email: Optional[str] = None  # Required for email_sow
    orb_api_key: Optional[str] = None  # Required for deploy_orb
    orb_plan_id: Optional[str] = None  # Required for deploy_orb


@router.get("/product-data-sources", response_model=List[Dict[str, str]])
async def get_product_data_sources():
    return [
        {"tool_name": "Mixpanel", "logo": "https://cdn.worldvectorlogo.com/logos/mixpanel.svg"},
        {"tool_name": "Google Analytics", "logo": "https://cdn.worldvectorlogo.com/logos/google-analytics.svg"},
        {"tool_name": "Amplitude", "logo": "https://cdn.worldvectorlogo.com/logos/amplitude.svg"},
        {"tool_name": "Segment", "logo": "https://cdn.worldvectorlogo.com/logos/segment-1.svg"},
        {"tool_name": "PostHog", "logo": "https://cdn.worldvectorlogo.com/logos/posthog.svg"},
        {"tool_name": "Pendo", "logo": "https://cdn.worldvectorlogo.com/logos/pendo.svg"},
        {"tool_name": "Fullstory", "logo": "https://cdn.worldvectorlogo.com/logos/fullstory.svg"},
        {"tool_name": "Hotjar", "logo": "https://cdn.worldvectorlogo.com/logos/hotjar.svg"}
    ]


@router.get("/customer-data-platform-sources", response_model=List[Dict[str, str]])
async def get_customer_data_platform_sources():
    return [
        {"tool_name": "Twilio Segment", "logo": "https://cdn.worldvectorlogo.com/logos/twilio.svg"},
        {"tool_name": "mParticle", "logo": "https://cdn.worldvectorlogo.com/logos/mparticle.svg"},
        {"tool_name": "Adobe Experience Platform", "logo": "https://cdn.worldvectorlogo.com/logos/adobe-2.svg"},
        {"tool_name": "Tealium", "logo": "https://cdn.worldvectorlogo.com/logos/tealium.svg"},
        {"tool_name": "BlueConic", "logo": "https://cdn.worldvectorlogo.com/logos/blueconic.svg"},
        {"tool_name": "Treasure Data", "logo": "https://cdn.worldvectorlogo.com/logos/treasure-data.svg"},
        {"tool_name": "ActionIQ", "logo": "https://cdn.worldvectorlogo.com/logos/actioniq.svg"},
        {"tool_name": "Lytics", "logo": "https://cdn.worldvectorlogo.com/logos/lytics.svg"},
        {"tool_name": "Bloomreach", "logo": "https://cdn.worldvectorlogo.com/logos/bloomreach.svg"},
        {"tool_name": "Simon Data", "logo": "https://cdn.worldvectorlogo.com/logos/simon-data.svg"},
        {"tool_name": "Zeotap", "logo": "https://cdn.worldvectorlogo.com/logos/zeotap.svg"},
        {"tool_name": "Rudderstack", "logo": "https://cdn.worldvectorlogo.com/logos/rudderstack.svg"}
    ]


@router.get("/revenue-data-sources", response_model=List[Dict[str, str]])
async def get_revenue_data_sources():
    return [
        {"tool_name": "Stripe", "logo": "https://cdn.worldvectorlogo.com/logos/stripe-2.svg"},
        {"tool_name": "PayPal", "logo": "https://cdn.worldvectorlogo.com/logos/paypal-2.svg"},
        {"tool_name": "Chargebee", "logo": "https://cdn.worldvectorlogo.com/logos/chargebee.svg"},
        {"tool_name": "Recurly", "logo": "https://cdn.worldvectorlogo.com/logos/recurly.svg"},
        {"tool_name": "Zuora", "logo": "https://cdn.worldvectorlogo.com/logos/zuora.svg"},
        {"tool_name": "ChartMogul", "logo": "https://cdn.worldvectorlogo.com/logos/chartmogul.svg"},
        {"tool_name": "ProfitWell", "logo": "https://cdn.worldvectorlogo.com/logos/profitwell.svg"},
        {"tool_name": "RevenueCat", "logo": "https://cdn.worldvectorlogo.com/logos/revenuecat.svg"},
        {"tool_name": "Paddle", "logo": "https://cdn.worldvectorlogo.com/logos/paddle.svg"},
        {"tool_name": "Square", "logo": "https://cdn.worldvectorlogo.com/logos/square.svg"}
    ]


@router.post("/generate-tool-config")
async def generate_tool_config(request: ToolConfigRequest):
    # Define all available tools
    product_tools = ["Mixpanel", "Google Analytics", "Amplitude", "Segment", "PostHog", "Pendo", "Fullstory", "Hotjar"]
    customer_tools = ["Twilio Segment", "mParticle", "Adobe Experience Platform", "Tealium", "BlueConic", 
                     "Treasure Data", "ActionIQ", "Lytics", "Bloomreach", "Simon Data", "Zeotap", "Rudderstack"]
    revenue_tools = ["Stripe", "PayPal", "Chargebee", "Recurly", "Zuora", "ChartMogul", "ProfitWell", 
                    "RevenueCat", "Paddle", "Square"]
    
    # Validate each tool against its respective category
    if request.product_tool not in product_tools:
        raise HTTPException(status_code=400, detail=f"Product tool '{request.product_tool}' not found in available product tools")
    
    if request.customer_tool not in customer_tools:
        raise HTTPException(status_code=400, detail=f"Customer tool '{request.customer_tool}' not found in available customer tools")
    
    if request.revenue_tool not in revenue_tools:
        raise HTTPException(status_code=400, detail=f"Revenue tool '{request.revenue_tool}' not found in available revenue tools")
    
    # Generate single comprehensive configuration
    config_data = generate_llms_integrator_primer(
        request.product_tool,
        request.customer_tool,
        request.revenue_tool
    )
    
    return config_data.model_dump()


@router.post("/deploy-github-to-lambda")
async def deploy_github_to_lambda(request: GitHubDeploymentRequest):
    if not request.github_url:
        raise HTTPException(status_code=400, detail="GitHub URL is required")
    
    # Basic URL validation
    if not (request.github_url.startswith("https://github.com/") or 
            request.github_url.startswith("git@github.com:")):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL format")
    
    try:
        result = deploy_github_repo_to_lambda(request.github_url)
        
        if result["success"]:
            return {
                "status": "success",
                "function_name": result["function_name"],
                "function_arn": result.get("function_arn"),
                "schedule_rule": result.get("schedule_rule"),
                "message": result["message"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@router.get("/lambda-deployment-status/{function_name}")
async def get_lambda_deployment_status(function_name: str):
    try:
        status = get_deployment_status(function_name)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deployment status: {str(e)}")




@router.post("/pricing-golive")
async def pricing_golive_action(request: GoLiveActionRequest):
    if request.action_type not in ["email_sow", "deploy_orb"]:
        raise HTTPException(
            status_code=400, 
            detail="Action type must be either 'email_sow' or 'deploy_orb'"
        )
    
    # Validate product exists
    validation_result = validate_product_exists(request.product_id)
    if not validation_result["success"]:
        if "not found" in validation_result["message"]:
            raise HTTPException(status_code=404, detail=validation_result["message"])
        else:
            raise HTTPException(status_code=400, detail=validation_result["message"])
    
    action_result = {}
    action_status = "pending"
    
    if request.action_type == "email_sow":
        if not request.customer_email:
            raise HTTPException(
                status_code=400,
                detail="Customer email is required for email_sow action"
            )
        
        try:
            email_results = send_enterprise_sow_email(
                request.pricing_data,
                request.customer_email
            )
            
            action_result = {
                "email_results": email_results,
                "action": "email_sow"
            }
            action_status = "success"
            
            # Save to MongoDB
            mongo_result = save_golive_action_to_product(
                request.product_id, 
                request, 
                action_result, 
                action_status
            )
            
            return {
                "status": "success",
                "action": "email_sow",
                "email_results": email_results,
                "product_id": request.product_id,
                "mongo_save_result": mongo_result,
                "message": "Enterprise SoW emails have been sent and action saved to product"
            }
            
        except Exception as e:
            action_status = "failed"
            action_result = {
                "error": str(e),
                "action": "email_sow"
            }
            
            # Save failed attempt to MongoDB
            save_golive_action_to_product(
                request.product_id, 
                request, 
                action_result, 
                action_status
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send enterprise SoW emails: {str(e)}"
            )
    
    elif request.action_type == "deploy_orb":
        if not request.orb_api_key or not request.orb_plan_id:
            raise HTTPException(
                status_code=400,
                detail="Orb API key and plan ID are required for deploy_orb action"
            )
        
        try:
            orb_result = deploy_pricing_to_orb(
                request.pricing_data,
                request.orb_api_key,
                request.orb_plan_id
            )
            
            if orb_result["success"]:
                action_result = {
                    "orb_result": orb_result,
                    "action": "deploy_orb"
                }
                action_status = "success"
                
                # Save to MongoDB
                mongo_result = save_golive_action_to_product(
                    request.product_id, 
                    request, 
                    action_result, 
                    action_status
                )
                
                return {
                    "status": "success",
                    "action": "deploy_orb",
                    "orb_result": orb_result,
                    "product_id": request.product_id,
                    "mongo_save_result": mongo_result,
                    "message": "Pricing successfully deployed to Orb and action saved to product"
                }
            else:
                action_status = "failed"
                action_result = {
                    "orb_result": orb_result,
                    "action": "deploy_orb"
                }
                
                # Save failed attempt to MongoDB
                save_golive_action_to_product(
                    request.product_id, 
                    request, 
                    action_result, 
                    action_status
                )
                
                raise HTTPException(
                    status_code=500,
                    detail=orb_result["message"]
                )
                
        except Exception as e:
            action_status = "failed" 
            action_result = {
                "error": str(e),
                "action": "deploy_orb"
            }
            
            # Save failed attempt to MongoDB
            save_golive_action_to_product(
                request.product_id, 
                request, 
                action_result, 
                action_status
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to deploy pricing to Orb: {str(e)}"
            )


@router.get("/product/{product_id}/golive-actions")
async def get_product_golive_actions_endpoint(product_id: str):
    result = get_product_golive_actions(product_id)
    
    if result["success"]:
        return {
            "product_id": result["product_id"],
            "product_name": result["product_name"],
            "go_live_actions": result["go_live_actions"],
            "total_actions": result["total_actions"]
        }
    else:
        if "not found" in result["message"]:
            raise HTTPException(status_code=404, detail=result["message"])
        else:
            raise HTTPException(status_code=500, detail=result["message"])

