from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import json
import os
from datetime import datetime, timezone
from datastore.api_types import ProductAPI, SuccessResponseAPI, DeleteRequestAPI
from datastore.models import Product, PricingExperimentRequest, PricingExperimentRuns

router = APIRouter()

@router.get("/products", response_model=List[ProductAPI])
async def get_all_products():
    try:
        products = []
        
        # Try to fetch products from database
        try:
            db_products = Product.objects()
            for product in db_products:
                product_api = ProductAPI(
                    _id=str(product.id),
                    name=product.product_name or "",
                    icp_description=product.product_icp_summary or "",
                    unit_level_cogs=None,
                    features_description_summary=product.product_description or "",
                    competitors=[],
                    product_documentations=product.product_marketing_docs or [],
                    vector_store_id=product.product_marketing_docs_vs_id,
                    created_at=None,
                    updated_at=None
                )
                products.append(product_api)
        except Exception:
            # Fallback to sample data from JSON if database query fails
            try:
                json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "product_data.json")
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                        product_data = data.get("product", {})
                        if product_data:
                            sample_product = ProductAPI(
                                _id="sample_product_1",
                                name=product_data.get("name", ""),
                                icp_description=product_data.get("icp_description", ""),
                                unit_level_cogs=product_data.get("unit_level_cogs", ""),
                                features_description_summary=product_data.get("features_description_summary", ""),
                                competitors=[],
                                product_documentations=product_data.get("product_documentations", []),
                                vector_store_id=None,
                                created_at=None,
                                updated_at=None
                            )
                            products.append(sample_product)
            except Exception:
                pass
        
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/experiments")
async def get_experiments_by_product_ids(product_ids: List[str] = Query(...)):
    try:
        experiments_data = []
        
        for product_id in product_ids:
            # Get the product first to validate it exists
            try:
                product = Product.objects(id=product_id).first()
                if not product:
                    continue
                
                # Get all experiment requests for this product
                experiment_requests = PricingExperimentRequest.objects(product=product)
                
                for exp_request in experiment_requests:
                    # Get all runs for this experiment request
                    experiment_runs = PricingExperimentRuns.objects(experiment_request=exp_request)
                    
                    for exp_run in experiment_runs:
                        experiment_data = {
                            "run_id": str(exp_run.id),
                            "request_id": str(exp_request.id),
                            "product_name": product.product_name,
                            "product_id": str(product.id),
                            "experiment_number": exp_request.experiment_number,
                            "experiment_gen_stage": exp_run.experiment_gen_stage,
                            "request_gen_stage": exp_request.experiment_gen_stage if exp_request.experiment_gen_stage else None,
                            "objective": exp_request.objective if exp_request.objective else None,
                            "usecase": exp_request.usecase if exp_request.usecase else None,
                            "positioning_summary": exp_run.positioning_summary if exp_run.positioning_summary else None,
                            "usage_summary": exp_run.usage_summary if exp_run.usage_summary else None,
                            "roi_gaps": exp_run.roi_gaps if exp_run.roi_gaps else None,
                            "experimental_pricing_plan": exp_run.experimental_pricing_plan if exp_run.experimental_pricing_plan else None,
                            "simulation_result": exp_run.simulation_result if exp_run.simulation_result else None,
                            "usage_projections": [
                                {
                                    "usage_value_in_units": proj.usage_value_in_units,
                                    "usage_unit": proj.usage_unit,
                                    "target_date": str(proj.target_date) if proj.target_date else None
                                } for proj in exp_run.usage_projections
                            ] if exp_run.usage_projections else None,
                            "revenue_projections": [
                                {
                                    "usage_value_in_units": proj.usage_value_in_units,
                                    "usage_unit": proj.usage_unit,
                                    "target_date": str(proj.target_date) if proj.target_date else None
                                } for proj in exp_run.revenue_projections
                            ] if exp_run.revenue_projections else None,
                            "cashflow_feasibility_comments": exp_run.cashflow_feasibility_comments if exp_run.cashflow_feasibility_comments else None,
                            "cashflow_no_negative_impact_approval_given": exp_run.cashflow_no_negative_impact_approval_given,
                            "experiment_feedback_summary": exp_run.experiment_feedback_summary if exp_run.experiment_feedback_summary else None,
                            "experiment_is_deployed": exp_run.experiment_is_deployed,
                            "experiment_deployed_on": str(exp_run.experiment_deployed_on) if exp_run.experiment_deployed_on else None,
                            "run_created_on": str(exp_run.created_on) if exp_run.created_on else None,
                            "request_created_on": str(exp_request.created_on) if exp_request.created_on else None,
                            "relevant_segments": [
                                {
                                    "segment_name": seg.segment_name,
                                    "segment_cdp_uid": seg.segment_cdp_uid,
                                    "segment_description": seg.segment_description,
                                    "segment_filter_logic": seg.segment_filter_logic,
                                    "segment_usage_summary": seg.segment_usage_summary,
                                    "segment_revenue_attribution_summary": seg.segment_revenue_attribution_summary
                                } for seg in exp_run.relevant_segments
                            ] if exp_run.relevant_segments else None
                        }
                        experiments_data.append(experiment_data)
            
            except Exception:
                # Skip this product ID if there's an error
                continue
        
        return {"experiments": experiments_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products", response_model=ProductAPI)
async def create_product(product: ProductAPI):
    try:
        # Create new product in database
        current_time = datetime.now(timezone.utc)
        new_product = Product(
            product_name=product.name,
            product_industry=None,
            product_description=product.features_description_summary,
            product_icp_summary=product.icp_description,
            product_categories=[],
            product_feature_docs=[],
            product_marketing_docs=product.product_documentations or [],
            product_technical_docs=[],
            product_usage_docs=[],
            product_competitors=[]
        )
        new_product.save()
        
        # Return the created product
        result = ProductAPI(
            _id=str(new_product.id),
            name=new_product.product_name or "",
            icp_description=new_product.product_icp_summary or "",
            unit_level_cogs=product.unit_level_cogs,
            features_description_summary=new_product.product_description or "",
            competitors=product.competitors or [],
            product_documentations=new_product.product_marketing_docs or [],
            vector_store_id=new_product.product_marketing_docs_vs_id,
            created_at=current_time.isoformat(),
            updated_at=current_time.isoformat()
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/products/{product_id}", response_model=ProductAPI)
async def update_product(product_id: str, product: ProductAPI):
    try:
        # Find the existing product
        existing_product = Product.objects(id=product_id).first()
        if not existing_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Update fields
        current_time = datetime.now(timezone.utc)
        update_data = {}
        
        if product.name:
            update_data["set__product_name"] = product.name
        if product.icp_description:
            update_data["set__product_icp_summary"] = product.icp_description
        if product.features_description_summary:
            update_data["set__product_description"] = product.features_description_summary
        if product.product_documentations:
            update_data["set__product_marketing_docs"] = product.product_documentations
        
        # Apply updates
        Product.objects(id=product_id).update(**update_data)
        
        # Fetch updated product
        updated_product = Product.objects(id=product_id).first()
        
        # Return the updated product
        result = ProductAPI(
            _id=str(updated_product.id),
            name=updated_product.product_name or "",
            icp_description=updated_product.product_icp_summary or "",
            unit_level_cogs=product.unit_level_cogs,
            features_description_summary=updated_product.product_description or "",
            competitors=product.competitors or [],
            product_documentations=updated_product.product_marketing_docs or [],
            vector_store_id=updated_product.product_marketing_docs_vs_id,
            created_at=None,
            updated_at=current_time.isoformat()
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/products/{product_id}", response_model=SuccessResponseAPI)
async def delete_product(product_id: str):
    try:
        # Find the existing product
        existing_product = Product.objects(id=product_id).first()
        if not existing_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Delete the product
        existing_product.delete()
        
        return SuccessResponseAPI(success=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
