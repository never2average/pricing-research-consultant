from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timezone
from datastore.types import CustomerSegmentResponse
from datastore.models import CustomerSegment

router = APIRouter()

@router.get("/customer-segments", response_model=List[CustomerSegmentResponse])
async def get_customer_segments():
    try:
        segments = []
        db_segments = CustomerSegment.objects()
        
        for segment in db_segments:
            segment_api = CustomerSegmentResponse(
                _id=str(segment.id),
                product=None,
                customer_segment_uid=segment.segment_cdp_uid or "",
                customer_segment_name=segment.segment_name or "",
                customer_segment_description=segment.segment_description or "",
                created_at=None,
                updated_at=None
            )
            segments.append(segment_api)
        
        return segments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer-segments/{segment_id}", response_model=CustomerSegmentResponse)
async def get_customer_segment(segment_id: str):
    try:
        segment = CustomerSegment.objects(id=segment_id).first()
        if not segment:
            raise HTTPException(status_code=404, detail="Customer segment not found")
        
        return CustomerSegmentResponse(
            _id=str(segment.id),
            product=None,
            customer_segment_uid=segment.segment_cdp_uid or "",
            customer_segment_name=segment.segment_name or "",
            customer_segment_description=segment.segment_description or "",
            created_at=None,
            updated_at=None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customer-segments", response_model=CustomerSegmentResponse)
async def create_customer_segment(segment: CustomerSegmentResponse):
    try:
        # Create new customer segment in database
        new_segment = CustomerSegment(
            segment_name=segment.customer_segment_name,
            segment_cdp_uid=segment.customer_segment_uid,
            segment_description=segment.customer_segment_description,
            segment_filter_logic=None,
            segment_usage_summary=None,
            segment_revenue_attribution_summary=None
        )
        new_segment.save()
        
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Return the created segment
        return CustomerSegmentResponse(
            _id=str(new_segment.id),
            product=segment.product,
            customer_segment_uid=new_segment.segment_cdp_uid or "",
            customer_segment_name=new_segment.segment_name or "",
            customer_segment_description=new_segment.segment_description or "",
            created_at=current_time,
            updated_at=current_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/customer-segments/{segment_id}", response_model=CustomerSegmentResponse)
async def update_customer_segment(segment_id: str, segment: CustomerSegmentResponse):
    try:
        # Find the existing segment
        existing_segment = CustomerSegment.objects(id=segment_id).first()
        if not existing_segment:
            raise HTTPException(status_code=404, detail="Customer segment not found")
        
        # Update fields
        update_data = {}
        
        if segment.customer_segment_name:
            update_data["set__segment_name"] = segment.customer_segment_name
        if segment.customer_segment_uid:
            update_data["set__segment_cdp_uid"] = segment.customer_segment_uid
        if segment.customer_segment_description:
            update_data["set__segment_description"] = segment.customer_segment_description
        
        # Apply updates
        if update_data:
            CustomerSegment.objects(id=segment_id).update(**update_data)
        
        # Fetch updated segment
        updated_segment = CustomerSegment.objects(id=segment_id).first()
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Return the updated segment
        return CustomerSegmentResponse(
            _id=str(updated_segment.id),
            product=segment.product,
            customer_segment_uid=updated_segment.segment_cdp_uid or "",
            customer_segment_name=updated_segment.segment_name or "",
            customer_segment_description=updated_segment.segment_description or "",
            created_at=segment.created_at,
            updated_at=current_time
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/customer-segments/{segment_id}")
async def delete_customer_segment(segment_id: str):
    try:
        # Find the existing segment
        existing_segment = CustomerSegment.objects(id=segment_id).first()
        if not existing_segment:
            raise HTTPException(status_code=404, detail="Customer segment not found")
        
        # Delete the segment
        existing_segment.delete()
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
