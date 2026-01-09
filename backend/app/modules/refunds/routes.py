from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.modules.refunds import schemas, service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/refunds", tags=["Refunds"])

@router.get("", response_model=List[schemas.RefundResponse])
def get_refunds(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all refunds with optional status filter
    
    Query Parameters:
    - status: Filter by status (Pending, Approved, Rejected, Completed)
    - skip: Number of records to skip
    - limit: Number of records to return
    """
    try:
        refunds = service.get_all_refunds(db, skip=skip, limit=limit, status=status)
        
        result = []
        for refund in refunds:
            result.append(_format_refund_response(refund))
        
        return result
    except Exception as e:
        logger.exception("[REFUNDS] Error fetching refunds")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{refund_id}", response_model=schemas.RefundResponse)
def get_refund(refund_id: int, db: Session = Depends(get_db)):
    """Get a specific refund by ID"""
    refund = service.get_refund_by_id(db, refund_id)
    
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    
    return _format_refund_response(refund)


@router.post("", response_model=schemas.RefundResponse)
def create_refund(refund: schemas.RefundCreate, db: Session = Depends(get_db)):
    """Create a new refund request"""
    try:
        new_refund = service.create_refund(
            db,
            order_id=refund.order_id,
            reason=refund.reason,
            amount=refund.amount,
            proof_image_path=refund.proof_image_path
        )
        
        # Fetch with order details
        created_refund = service.get_refund_by_id(db, new_refund.id)
        
        return _format_refund_response(created_refund)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("[REFUNDS] Error creating refund")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{refund_id}/status", response_model=schemas.RefundResponse)
def update_refund_status(
    refund_id: int, 
    status_update: schemas.RefundStatusUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update refund status (Pending, Approved, Completed)
    Note: For 'Rejected' status, please use the /reject endpoint to provide a reason.
    """
    if status_update.status == 'Rejected':
        raise HTTPException(
            status_code=400, 
            detail="To reject a refund, please use the /reject endpoint and provide a reason."
        )
        
    refund = service.update_refund_status(db, refund_id, status_update.status)
    
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    
    # Fetch with order details
    updated_refund = service.get_refund_by_id(db, refund_id)
    
    return _format_refund_response(updated_refund)


@router.post("/{refund_id}/reject", response_model=schemas.RefundResponse)
def reject_refund(
    refund_id: int,
    rejection: schemas.RefundReject,
    db: Session = Depends(get_db)
):
    """
    Reject a refund request with a mandatory reason.
    This triggers a rejection email to the customer.
    """
    refund = service.reject_refund(
        db, 
        refund_id, 
        rejection_reason=rejection.rejection_reason,
        admin_notes=rejection.admin_notes
    )
    
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
        
    # Fetch with order details
    updated_refund = service.get_refund_by_id(db, refund_id)
    
    return _format_refund_response(updated_refund)


def _format_refund_response(refund):
    """Helper to format refund response since schema is complex"""
    return {
        "id": refund.id,
        "order_id": refund.order_id,
        "order_number": refund.order.order_id if refund.order else None,
        "customer_name": refund.order.customer_name if refund.order else None,
        "phone": refund.order.phone if refund.order else None,
        "email": refund.order.email if refund.order else None,
        "address": refund.order.address if refund.order else None,
        "city": refund.order.city if refund.order else None,
        "state": refund.order.state if refund.order else None,
        "pincode": refund.order.pincode if refund.order else None,
        "products": refund.order.products if refund.order else None,
        "reason": refund.reason,
        "amount": float(refund.amount),
        "status": refund.status,
        "proof_image_path": refund.proof_image_path,
        "return_awb_number": refund.return_awb_number,
        "return_label_path": refund.return_label_path,
        "return_delivery_status": refund.return_delivery_status,
        
        # New fields
        "rejection_reason": refund.rejection_reason,
        "admin_notes": refund.admin_notes,
        
        "created_at": refund.created_at,
        "updated_at": refund.updated_at,
        "approved_at": refund.approved_at,
        "completed_at": refund.completed_at,
    }


@router.put("/{refund_id}/awb", response_model=schemas.RefundResponse)
def update_refund_awb(
    refund_id: int, 
    awb_update: schemas.RefundAWBUpdate, 
    db: Session = Depends(get_db)
):
    """Update refund with return AWB number and label path"""
    refund = service.update_refund_awb(
        db, 
        refund_id, 
        awb_update.return_awb_number, 
        awb_update.return_label_path
    )
    
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    
    # Fetch with order details
    updated_refund = service.get_refund_by_id(db, refund_id)
    
    refund_dict = {
        "id": updated_refund.id,
        "order_id": updated_refund.order_id,
        "order_number": updated_refund.order.order_id if updated_refund.order else None,
        "customer_name": updated_refund.order.customer_name if updated_refund.order else None,
        "phone": updated_refund.order.phone if updated_refund.order else None,
        "email": updated_refund.order.email if updated_refund.order else None,
        "address": updated_refund.order.address if updated_refund.order else None,
        "city": updated_refund.order.city if updated_refund.order else None,
        "state": updated_refund.order.state if updated_refund.order else None,
        "pincode": updated_refund.order.pincode if updated_refund.order else None,
        "products": updated_refund.order.products if updated_refund.order else None,
        "reason": updated_refund.reason,
        "amount": float(updated_refund.amount),
        "status": updated_refund.status,
        "proof_image_path": updated_refund.proof_image_path,
        "return_awb_number": updated_refund.return_awb_number,
        "return_label_path": updated_refund.return_label_path,
        "return_delivery_status": updated_refund.return_delivery_status,
        "created_at": updated_refund.created_at,
        "updated_at": updated_refund.updated_at,
        "approved_at": updated_refund.approved_at,
        "completed_at": updated_refund.completed_at,
    }
    
    return refund_dict


@router.delete("/{refund_id}")
def delete_refund(refund_id: int, db: Session = Depends(get_db)):
    """Delete a refund request"""
    success = service.delete_refund(db, refund_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Refund not found")
    
    return {"message": "Refund deleted successfully"}
