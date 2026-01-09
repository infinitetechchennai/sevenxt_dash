from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas
from app.modules.delivery.shipment_service import create_exchange_return_shipment, create_exchange_forward_shipment
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def create_exchange(db: Session, exchange_data: schemas.ExchangeCreate) -> models.Exchange:
    """Create a new exchange request for same product replacement"""
    
    new_exchange = models.Exchange(
        order_id=exchange_data.order_id,
        reason=exchange_data.reason,
        description=exchange_data.description,
        proof_image_path=exchange_data.proof_image_path,
        product_id=exchange_data.product_id,
        product_name=exchange_data.product_name,
        variant_color=exchange_data.variant_color,
        quantity=exchange_data.quantity,
        price=exchange_data.price,
        status='Pending'
    )
    
    db.add(new_exchange)
    
    # Update Order Status to 'Exchange Requested'
    if new_exchange.order:
        new_exchange.order.status = 'Exchange Requested'
    else:
        # Fallback if relationship not yet loaded (though it should be if attached to session, but safe to query)
        from app.modules.orders.models import Order
        order = db.query(Order).filter(Order.order_id == exchange_data.order_id).first()
        if order:
            order.status = 'Exchange Requested'

    db.commit()
    db.refresh(new_exchange)
    
    logger.info(f"Created exchange ID {new_exchange.id} for order {exchange_data.order_id} - Product: {exchange_data.product_name}")
    return new_exchange


def get_all_exchanges(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[models.Exchange]:
    """Get all exchanges with optional status filter"""
    query = db.query(models.Exchange)
    
    if status:
        query = query.filter(models.Exchange.status == status)
    
    return query.order_by(models.Exchange.created_at.desc()).offset(skip).limit(limit).all()


def get_exchange_by_id(db: Session, exchange_id: int) -> Optional[models.Exchange]:
    """Get exchange by ID"""
    return db.query(models.Exchange).filter(models.Exchange.id == exchange_id).first()


def get_exchange_by_order_id(db: Session, order_id: str) -> List[models.Exchange]:
    """Get all exchanges for a specific order"""
    return db.query(models.Exchange).filter(models.Exchange.order_id == order_id).all()


def update_exchange_status(db: Session, exchange_id: int, status: str, admin_notes: Optional[str] = None) -> Optional[models.Exchange]:
    """Update exchange status"""
    exchange = get_exchange_by_id(db, exchange_id)
    if not exchange:
        return None
    
    exchange.status = status
    if admin_notes:
        exchange.admin_notes = admin_notes
    exchange.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(exchange)
    
    logger.info(f"Updated exchange {exchange_id} status to {status}")
    return exchange


def approve_exchange(db: Session, exchange_id: int) -> Optional[models.Exchange]:
    """Admin approves exchange and schedules return"""
    exchange = get_exchange_by_id(db, exchange_id)
    if not exchange:
        return None
    
    # Generate Return AWB
    awb, label_path = create_exchange_return_shipment(db, exchange)
    
    exchange.status = 'Approved'
    exchange.approved_at = datetime.utcnow()
    exchange.updated_at = datetime.utcnow()
    
    if awb:
        exchange.return_awb_number = awb
        exchange.return_label_path = label_path
        exchange.return_delivery_status = 'Pickup Scheduled'
        
        # Update Order Status to indicate Return is active
        if exchange.order:
            exchange.order.status = 'Exchange Approved'
    
    db.commit()
    db.refresh(exchange)
    
    logger.info(f"Exchange {exchange_id} approved. Return AWB: {awb}")
    return exchange


def reject_exchange(db: Session, exchange_id: int, rejection_reason: str) -> Optional[models.Exchange]:
    """Admin rejects exchange and sends rejection email to customer"""
    exchange = get_exchange_by_id(db, exchange_id)
    if not exchange:
        return None
    
    # Update exchange status to Rejected
    exchange.status = 'Rejected'
    exchange.admin_notes = f"Rejection Reason: {rejection_reason}"
    exchange.updated_at = datetime.utcnow()
    
    # Update Order Status
    if exchange.order:
        exchange.order.status = 'Exchange Rejected'
    
    db.commit()
    db.refresh(exchange)
    
    # Send rejection email to customer
    try:
        from app.modules.auth.sendgrid_utils import sendgrid_service
        
        customer_email = exchange.order.email if exchange.order else None
        customer_name = exchange.order.customer_name if exchange.order else "Customer"
        
        if customer_email:
            sendgrid_service.send_exchange_rejection_email(
                to_email=customer_email,
                customer_name=customer_name,
                order_id=exchange.order_id,
                product_name=exchange.product_name,
                rejection_reason=rejection_reason
            )
            logger.info(f"Rejection email sent to {customer_email} for exchange {exchange_id}")
        else:
            logger.warning(f"No email found for exchange {exchange_id}, skipping email notification")
    except Exception as e:
        logger.error(f"Failed to send rejection email for exchange {exchange_id}: {e}")
    
    logger.info(f"Exchange {exchange_id} rejected. Reason: {rejection_reason}")
    return exchange



def process_exchange_replacement(db: Session, exchange_id: int) -> Optional[models.Exchange]:
    """Process exchange replacement: Generate new AWB and overwrite order AWB"""
    exchange = get_exchange_by_id(db, exchange_id)
    if not exchange:
        return None
        
    # Generate Forward AWB
    awb, label_path = create_exchange_forward_shipment(db, exchange)
    
    if awb:
        exchange.new_awb_number = awb
        exchange.new_label_path = label_path
        exchange.new_delivery_status = 'Ready to Pickup'
        exchange.status = 'New Product Dispatched'
        
        # Update Parent Order to 'Ready to Pickup' and set new AWB
        # This makes it appear in the main Orders list as a new shipment ready for processing
        if exchange.order:
            exchange.order.status = 'Ready to Pickup'
            exchange.order.awb_number = awb
            exchange.order.updated_at = datetime.utcnow()
            logger.info(f"Updated Order {exchange.order.order_id} status to 'Ready to Pickup' with new AWB {awb}")
        
        db.commit()
        db.refresh(exchange)
        logger.info(f"Exchange {exchange_id} processed. New AWB: {awb}")
        return exchange
    else:
        logger.error(f"Failed to generate forward AWB for exchange {exchange_id}")
        return None


def quality_check_exchange(
    db: Session, 
    exchange_id: int, 
    approved: bool, 
    notes: Optional[str] = None
) -> Optional[models.Exchange]:
    """Admin performs quality check on returned product"""
    exchange = get_exchange_by_id(db, exchange_id)
    if not exchange:
        return None
    
    exchange.quality_approved = 1 if approved else 0
    exchange.quality_checked_at = datetime.utcnow()
    exchange.quality_check_notes = notes
    exchange.updated_at = datetime.utcnow()
    
    if approved:
        exchange.status = 'Quality Check Passed'
        db.commit() # Commit first before processing replacement
        
        # Automatically trigger replacement process
        logger.info(f"Quality check passed for exchange {exchange_id}. Auto-triggering replacement.")
        return process_exchange_replacement(db, exchange_id)
    else:
        exchange.status = 'Quality Check Failed'
        # If failed, maybe update order status to 'Exchange Rejected'?
        if exchange.order:
            exchange.order.status = 'Exchange Rejected'
            
        db.commit()
        db.refresh(exchange)
    
    logger.info(f"Quality check for exchange {exchange_id}: {'Passed' if approved else 'Failed'}")
    return exchange


def refund_exchange(db: Session, exchange_id: int) -> Optional[models.Exchange]:
    """Process refund for exchange (if out of stock)"""
    exchange = get_exchange_by_id(db, exchange_id)
    if not exchange:
        return None
        
    exchange.status = 'Refunded'
    exchange.completed_at = datetime.utcnow()
    exchange.updated_at = datetime.utcnow()
    
    # Update parent order status
    if exchange.order:
        exchange.order.status = 'Refunded'
        exchange.order.updated_at = datetime.utcnow()
        logger.info(f"Order {exchange.order.order_id} status updated to 'Refunded'")
    
    db.commit()
    db.refresh(exchange)
    
    logger.info(f"Exchange {exchange_id} marked as Refunded")
    return exchange



def update_return_delivery_status(db: Session, exchange_id: int, delivery_status: str) -> Optional[models.Exchange]:
    """Update return delivery status from Delhivery webhook"""
    exchange = get_exchange_by_id(db, exchange_id)
    if not exchange:
        return None
    
    exchange.return_delivery_status = delivery_status
    exchange.updated_at = datetime.utcnow()
    
    # If delivered, mark as received
    if delivery_status == 'Delivered':
        exchange.status = 'Return Received'
    
    db.commit()
    db.refresh(exchange)
    
    logger.info(f"Updated return delivery status for exchange {exchange_id}: {delivery_status}")
    return exchange


def update_new_delivery_status(db: Session, exchange_id: int, delivery_status: str) -> Optional[models.Exchange]:
    """Update new product delivery status from Delhivery webhook"""
    exchange = get_exchange_by_id(db, exchange_id)
    if not exchange:
        return None
    
    exchange.new_delivery_status = delivery_status
    exchange.updated_at = datetime.utcnow()
    
    # If delivered, mark as completed
    if delivery_status == 'Delivered':
        exchange.status = 'Completed'
        exchange.completed_at = datetime.utcnow()
    
    # Sync with Parent Order Status
    if exchange.order:
        exchange.order.status = delivery_status
        logger.info(f"Updated Order {exchange.order.order_id} status to {delivery_status} (synced from Exchange)")
    
    db.commit()
    db.refresh(exchange)
    
    logger.info(f"Updated new product delivery status for exchange {exchange_id}: {delivery_status}")
    return exchange


def delete_exchange(db: Session, exchange_id: int) -> bool:
    """Delete an exchange"""
    exchange = get_exchange_by_id(db, exchange_id)
    if not exchange:
        return False
    
    db.delete(exchange)
    db.commit()
    
    logger.info(f"Deleted exchange {exchange_id}")
    return True
