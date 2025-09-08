import requests


def deploy_pricing_to_orb(pricing_data, orb_api_key, orb_plan_id):
    orb_base_url = "https://api.withorb.com/v1"
    headers = {
        "Authorization": f"Bearer {orb_api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepare pricing data for Orb API
    orb_pricing_data = {
        "plan_id": orb_plan_id,
        "name": pricing_data.pricing_name,
        "pricing_model": pricing_data.pricing_model,
        "effective_date": pricing_data.effective_date,
        "tiers": pricing_data.pricing_tiers,
        "customer_segments": pricing_data.customer_segments
    }
    
    try:
        # Deploy pricing configuration to Orb
        response = requests.post(
            f"{orb_base_url}/plans/{orb_plan_id}/pricing",
            headers=headers,
            json=orb_pricing_data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            return {
                "success": True,
                "orb_response": response.json(),
                "message": "Pricing successfully deployed to Orb"
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code,
                "message": f"Orb API error: {response.status_code}"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to connect to Orb API"
        }
