import os
import mongoengine
from datetime import datetime
from datastore.models import Product, GoLiveAction


def ensure_mongodb_connection():
    try:
        if not mongoengine.connection.get_connection():
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/pricing_research')
            mongoengine.connect(host=mongodb_uri)
    except Exception:
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/pricing_research')
        mongoengine.connect(host=mongodb_uri)


def save_golive_action_to_product(product_id, request, action_result, action_status):
    ensure_mongodb_connection()
    
    try:
        # Get the product document
        product = Product.objects.get(id=product_id)
        
        # Create GoLiveAction embedded document
        go_live_action = GoLiveAction(
            action_type=request.action_type,
            pricing_name=request.pricing_data.pricing_name,
            pricing_tiers=[tier for tier in request.pricing_data.pricing_tiers],
            pricing_model=request.pricing_data.pricing_model,
            effective_date=request.pricing_data.effective_date,
            customer_segments=request.pricing_data.customer_segments,
            customer_email=request.customer_email,
            orb_api_key=request.orb_api_key if request.orb_api_key else None,
            orb_plan_id=request.orb_plan_id if request.orb_plan_id else None,
            action_status=action_status,
            action_result=action_result,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add to product's go_live_actions list
        product.update(push__go_live_actions=go_live_action)
        
        return {
            "success": True,
            "message": "Go-live action saved to product document",
            "product_id": str(product.id)
        }
        
    except Product.DoesNotExist:
        return {
            "success": False,
            "message": f"Product with ID {product_id} not found"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to save go-live action: {str(e)}"
        }


def get_product_golive_actions(product_id):
    ensure_mongodb_connection()
    
    try:
        product = Product.objects.get(id=product_id)
        
        # Convert go_live_actions to dict for JSON response
        actions = []
        for action in product.go_live_actions:
            action_dict = {
                "action_type": action.action_type,
                "pricing_name": action.pricing_name,
                "pricing_model": action.pricing_model,
                "effective_date": action.effective_date,
                "customer_segments": action.customer_segments,
                "customer_email": action.customer_email,
                "action_status": action.action_status,
                "action_result": action.action_result,
                "created_at": action.created_at.isoformat() if action.created_at else None,
                "updated_at": action.updated_at.isoformat() if action.updated_at else None
            }
            actions.append(action_dict)
        
        return {
            "success": True,
            "product_id": str(product.id),
            "product_name": product.product_name,
            "go_live_actions": actions,
            "total_actions": len(actions)
        }
        
    except Product.DoesNotExist:
        return {
            "success": False,
            "message": f"Product with ID {product_id} not found"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to retrieve go-live actions: {str(e)}"
        }


def validate_product_exists(product_id):
    ensure_mongodb_connection()
    
    try:
        product = Product.objects.get(id=product_id)
        return {
            "success": True,
            "product": product
        }
    except Product.DoesNotExist:
        return {
            "success": False,
            "message": f"Product with ID {product_id} not found"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Invalid product ID format: {str(e)}"
        }
