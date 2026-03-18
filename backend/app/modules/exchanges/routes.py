from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from . import schemas, service
from app.modules.activity_logs.service import log_activity
from app.modules.auth.routes import get_current_employee
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exchanges", tags=["Exchanges"])


@router.post("", response_model=schemas.ExchangeResponse)
def create_exchange(
    exchange_data: schemas.ExchangeCreate,
    db: Session = Depends(get_db)
):
    """Create a new exchange request"""
    try:
        new_exchange = service.create_exchange(db, exchange_data)
        
        # Log activity
        log_activity(
            db=db,
            action="Created Exchange Request",
            module="Exchanges",
            user_name="Customer",
            user_type="System",
            details=f"Exchange request for order {exchange_data.order_id}: Replace {exchange_data.product_name} (Reason: {exchange_data.reason})",
            status="Success",
            affected_entity_type="Exchange",
            affected_entity_id=str(new_exchange.id)
        )
        
        return new_exchange
    except Exception as e:
        logger.exception("Error creating exchange")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[schemas.ExchangeResponse])
def get_exchanges(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all exchanges with optional status filter"""
    try:
        exchanges = service.get_all_exchanges(db, skip=skip, limit=limit, status=status)
        return exchanges
    except Exception as e:
        logger.exception("Error fetching exchanges")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{exchange_id}", response_model=schemas.ExchangeResponse)
def get_exchange(
    exchange_id: int,
    db: Session = Depends(get_db)
):
    """Get exchange by ID"""
    exchange = service.get_exchange_by_id(db, exchange_id)
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    return exchange


@router.get("/order/{order_id}", response_model=List[schemas.ExchangeResponse])
def get_exchanges_by_order(
    order_id: str,  # String like "ORD-B2C-123"
    db: Session = Depends(get_db)
):
    """Get all exchanges for a specific order"""
    exchanges = service.get_exchange_by_order_id(db, order_id)
    return exchanges


@router.put("/{exchange_id}/status", response_model=schemas.ExchangeResponse)
def update_exchange_status(
    exchange_id: int,
    status_update: schemas.ExchangeStatusUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_employee)
):
    """Update exchange status"""
    exchange = service.update_exchange_status(
        db, 
        exchange_id, 
        status_update.status, 
        status_update.admin_notes
    )
    
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    # Log activity
    log_activity(
        db=db,
        action="Updated Exchange Status",
        module="Exchanges",
        user_id=str(current_user.id),
        user_name=current_user.name,
        user_type=current_user.role.capitalize(),
        details=f"Changed exchange {exchange_id} status to '{status_update.status}'",
        status="Success",
        affected_entity_type="Exchange",
        affected_entity_id=str(exchange_id)
    )
    
    return exchange


@router.post("/{exchange_id}/approve", response_model=schemas.ExchangeResponse)
def approve_exchange(
    exchange_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_employee)
):
    """Admin approves exchange request"""
    exchange = service.approve_exchange(db, exchange_id)
    
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    # Log activity
    log_activity(
        db=db,
        action="Approved Exchange",
        module="Exchanges",
        user_id=str(current_user.id),
        user_name=current_user.name,
        user_type=current_user.role.capitalize(),
        details=f"Approved exchange {exchange_id}",
        status="Success",
        affected_entity_type="Exchange",
        affected_entity_id=str(exchange_id)
    )
    
    return exchange


@router.post("/{exchange_id}/reject", response_model=schemas.ExchangeResponse)
def reject_exchange(
    exchange_id: int,
    reject_data: schemas.ExchangeRejectRequest,
    db: Session = Depends(get_db)
):
    """Admin rejects exchange request and sends rejection email to customer"""
    exchange = service.reject_exchange(db, exchange_id, reject_data.rejection_reason)
    
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    # Log activity
    log_activity(
        db=db,
        action="Rejected Exchange",
        module="Exchanges",
        user_name="Admin",
        user_type="Admin",
        details=f"Rejected exchange {exchange_id}. Reason: {reject_data.rejection_reason}",
        status="Rejected",
        affected_entity_type="Exchange",
        affected_entity_id=str(exchange_id)
    )
    
    return exchange



@router.post("/{exchange_id}/quality-check", response_model=schemas.ExchangeResponse)
def quality_check(
    exchange_id: int,
    quality_data: schemas.QualityCheckRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_employee)
):
    """Admin performs quality check on returned product"""
    exchange = service.quality_check_exchange(
        db, 
        exchange_id, 
        quality_data.approved,
        quality_data.notes
    )
    
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    # Log activity
    action = "Quality Check Passed" if quality_data.approved else "Quality Check Failed"
    log_activity(
        db=db,
        action=action,
        module="Exchanges",
        user_id=str(current_user.id),
        user_name=current_user.name,
        user_type=current_user.role.capitalize(),
        details=f"Exchange {exchange_id} quality {'approved' if quality_data.approved else 'rejected'}",
        status="Success" if quality_data.approved else "Failed",
        affected_entity_type="Exchange",
        affected_entity_id=str(exchange_id)
    )
    
    return exchange


@router.post("/{exchange_id}/process-replacement", response_model=schemas.ExchangeResponse)
def process_replacement(
    exchange_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_employee)
):
    """Process exchange replacement (Generate new AWB)"""
    exchange = service.process_exchange_replacement(db, exchange_id)
    
    if not exchange:
        raise HTTPException(status_code=400, detail="Failed to process replacement or exchange not found")
    
    # Log activity
    log_activity(
        db=db,
        action="Processed Exchange Replacement",
        module="Exchanges",
        user_id=str(current_user.id),
        user_name=current_user.name,
        user_type=current_user.role.capitalize(),
        details=f"Generated new AWB {exchange.new_awb_number} for exchange {exchange_id}",
        status="Success",
        affected_entity_type="Exchange",
        affected_entity_id=str(exchange_id)
    )
    
    return exchange


@router.post("/{exchange_id}/refund", response_model=schemas.ExchangeResponse)
def refund_exchange_endpoint(
    exchange_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_employee)
):
    """Process refund for exchange (if out of stock)"""
    exchange = service.refund_exchange(db, exchange_id)
    
    if not exchange:
        raise HTTPException(status_code=400, detail="Failed to refund exchange or exchange not found")
    
    # Log activity
    log_activity(
        db=db,
        action="Refunded Exchange",
        module="Exchanges",
        user_id=str(current_user.id),
        user_name=current_user.name,
        user_type=current_user.role.capitalize(),
        details=f"Refunded exchange {exchange_id} (Out of Stock)",
        status="Success",
        affected_entity_type="Exchange",
        affected_entity_id=str(exchange_id)
    )
    
    return exchange


@router.delete("/{exchange_id}")
def delete_exchange(
    exchange_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_employee)
):
    """Delete an exchange"""
    success = service.delete_exchange(db, exchange_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    # Log activity
    log_activity(
        db=db,
        action="Deleted Exchange",
        module="Exchanges",
        user_id=str(current_user.id),
        user_name=current_user.name,
        user_type=current_user.role.capitalize(),
        details=f"Deleted exchange {exchange_id}",
        status="Success",
        affected_entity_type="Exchange",
        affected_entity_id=str(exchange_id)
    )
    
    return {"message": "Exchange deleted successfully"}
