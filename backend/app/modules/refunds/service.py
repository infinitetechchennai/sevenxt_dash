from sqlalchemy.orm import Session, joinedload
from app.modules.refunds.models import Refund
from app.modules.orders.models import Order
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_all_refunds(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Refund]:
    """Get all refunds with optional status filter"""
    query = db.query(Refund).options(joinedload(Refund.order))
    
    if status:
        query = query.filter(Refund.status == status)
    
    return query.order_by(Refund.created_at.desc()).offset(skip).limit(limit).all()


def get_refund_by_id(db: Session, refund_id: int) -> Optional[Refund]:
    """Get a specific refund by ID"""
    return db.query(Refund).options(joinedload(Refund.order)).filter(Refund.id == refund_id).first()


def create_refund(db: Session, order_id: int, reason: str, amount: float, proof_image_path: Optional[str] = None) -> Refund:
    """Create a new refund request"""
    # Verify order exists
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError(f"Order with id {order_id} not found")
    
    refund = Refund(
        order_id=order_id,
        reason=reason,
        amount=amount,
        status='Pending',
        proof_image_path=proof_image_path
    )
    
    db.add(refund)
    db.commit()
    db.refresh(refund)
    
    logger.info(f"[REFUND] Created refund request for order {order.order_id}")
    return refund


def update_refund_status(db: Session, refund_id: int, status: str) -> Optional[Refund]:
    """Update refund status and trigger return AWB generation if approved"""
    refund = db.query(Refund).options(joinedload(Refund.order)).filter(Refund.id == refund_id).first()
    
    if not refund:
        return None
    
    refund.status = status
    
    # Sync order status
    if refund.order:
        if status == 'Approved':
            refund.order.status = "Refund Approved"
        elif status == 'Completed':
            refund.order.status = "Refunded"
            
    # Set timestamps based on status
    if status == 'Approved':
        refund.approved_at = datetime.now()
        refund.return_delivery_status = 'Manifested'  # Initial status
        
        # 1. Send Approval Email
        try:
            from app.modules.auth.sendgrid_utils import sendgrid_service
            if refund.order and refund.order.email:
                sendgrid_service.send_refund_approval_email(
                    to_email=refund.order.email,
                    customer_name=refund.order.customer_name or "Customer",
                    order_id=refund.order.order_id,
                    amount=float(refund.amount)
                )
                logger.info(f"[REFUND] Approval email sent to {refund.order.email}")
        except Exception as e:
            logger.error(f"[REFUND] Failed to send approval email: {e}")
        
        # 2. TRIGGER RETURN AWB GENERATION
        try:
            from app.modules.delivery.shipment_service import create_return_shipment
            
            logger.info(f"[REFUND] Generating return AWB for refund {refund_id}")
            
            # Generate return AWB and send email
            return_awb, return_label = create_return_shipment(db, refund)
            
            if return_awb:
                refund.return_awb_number = return_awb
                refund.return_label_path = return_label
                logger.info(f"[REFUND] Return AWB generated: {return_awb}")
                logger.info(f"[REFUND] Return label saved: {return_label}")
                logger.info(f"[REFUND] Email sent to customer with return label")
            else:
                logger.error(f"[REFUND] Failed to generate return AWB - function returned None")
                # Don't fail the approval, just log the error
                
        except Exception as e:
            logger.exception(f"[REFUND] Error generating return AWB: {e}")
            import traceback
            logger.error(f"[REFUND] Full traceback: {traceback.format_exc()}")
            # Don't fail the approval, just log the error
            
    elif status == 'Completed':
        refund.completed_at = datetime.now()
    
    db.commit()
    db.refresh(refund)
    
    logger.info(f"[REFUND] Updated refund {refund_id} status to {status}")
    return refund


def reject_refund(db: Session, refund_id: int, rejection_reason: str, admin_notes: Optional[str] = None) -> Optional[Refund]:
    """Reject a refund request with a reason and send email"""
    refund = db.query(Refund).options(joinedload(Refund.order)).filter(Refund.id == refund_id).first()
    
    if not refund:
        return None
    
    # Update refund status
    refund.status = 'Rejected'
    refund.rejection_reason = rejection_reason
    refund.admin_notes = admin_notes
    
    # Update order status
    if refund.order:
        refund.order.status = "Refund Rejected"
    
    db.commit()
    db.refresh(refund)
    
    # Send Rejection Email
    try:
        from app.modules.auth.sendgrid_utils import sendgrid_service
        
        print(f"[DEBUG] Attempting to send rejection email to {refund.order.email}")
        print(f"[DEBUG] Reason: {rejection_reason}")
        
        if refund.order and refund.order.email:
            email_sent = sendgrid_service.send_refund_rejection_email(
                to_email=refund.order.email,
                customer_name=refund.order.customer_name or "Customer",
                order_id=refund.order.order_id,
                amount=float(refund.amount),
                rejection_reason=rejection_reason
            )
            
            if email_sent:
                logger.info(f"[REFUND] Rejection email sent successfully to {refund.order.email}")
            else:
                logger.error(f"[REFUND] Failed to send rejection email (function returned False)")
        else:
            logger.warning(f"[REFUND] No customer email found for order {refund.order_id}")
            
    except Exception as e:
        logger.exception(f"[REFUND] Error sending rejection email: {e}")
    
    logger.info(f"[REFUND] Rejected refund {refund_id}. Reason: {rejection_reason}")
    return refund


def update_refund_awb(db: Session, refund_id: int, return_awb_number: str, return_label_path: str) -> Optional[Refund]:
    """Update refund with return AWB number and label path"""
    refund = db.query(Refund).filter(Refund.id == refund_id).first()
    
    if not refund:
        return None
    
    refund.return_awb_number = return_awb_number
    refund.return_label_path = return_label_path
    
    db.commit()
    db.refresh(refund)
    
    logger.info(f"[REFUND] Updated refund {refund_id} with return AWB: {return_awb_number}")
    return refund


def delete_refund(db: Session, refund_id: int) -> bool:
    """Delete a refund request"""
    refund = db.query(Refund).filter(Refund.id == refund_id).first()
    
    if not refund:
        return False
    
    db.delete(refund)
    db.commit()
    
    logger.info(f"[REFUND] Deleted refund {refund_id}")
    return True
