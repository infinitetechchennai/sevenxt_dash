from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.modules.orders.models import Delivery, Order
from app.modules.exchanges.models import Exchange
from app.modules.refunds.models import Refund
from datetime import datetime
import logging

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)

# Add delivery router for pickup scheduling
delivery_router = APIRouter(prefix="/delivery", tags=["Delivery"])

@router.post("/delhivery")
async def delhivery_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Production-safe Delhivery Webhook Handler
    Handles Pickup → In-Transit → Delivered updates
    
    Security Features:
    - Signature verification (configurable)
    - IP whitelisting (configurable)
    - Request logging
    """
    from app.config import settings
    import hmac
    import hashlib
    
    # ========================================
    # SECURITY LAYER 1: IP Whitelisting
    # ========================================
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"[WEBHOOK] Request from IP: {client_ip}")
    
    if settings.WEBHOOK_ALLOWED_IPS and client_ip not in settings.WEBHOOK_ALLOWED_IPS:
        logger.warning(f"[WEBHOOK] ❌ Blocked request from unauthorized IP: {client_ip}")
        raise HTTPException(status_code=403, detail="Unauthorized IP address")
    
    # ========================================
    # SECURITY LAYER 2: Signature Verification
    # ========================================
    if settings.WEBHOOK_SIGNATURE_VERIFICATION_ENABLED:
        # Get signature from header
        signature = request.headers.get("X-Delhivery-Signature") or request.headers.get("X-Webhook-Signature")
        
        if not signature:
            logger.warning("[WEBHOOK] ❌ Missing webhook signature")
            raise HTTPException(status_code=401, detail="Missing webhook signature")
        
        # Get raw body for signature verification
        body = await request.body()
        
        # Calculate expected signature
        expected_signature = hmac.new(
            settings.DELHIVERY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Verify signature
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning(f"[WEBHOOK] ❌ Invalid signature. Expected: {expected_signature[:10]}..., Got: {signature[:10]}...")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        logger.info("[WEBHOOK] ✅ Signature verified successfully")
        
        # Parse JSON from body
        import json
        payload = json.loads(body.decode())
    else:
        # Testing mode - no signature verification
        logger.warning("[WEBHOOK] ⚠️ TESTING MODE - Signature verification disabled")
        payload = await request.json()
    
    logger.info(f"[WEBHOOK] Payload received: {payload}")

    # -------------------------
    # 1️⃣ Extract AWB & Status
    # -------------------------
    awb = None
    raw_status = None

    if "Shipment" in payload:
        shipment = payload.get("Shipment", {})
        awb = shipment.get("AWB") or shipment.get("waybill")

        status_block = shipment.get("Status")
        if isinstance(status_block, dict):
            raw_status = status_block.get("Status")
        elif isinstance(status_block, str):
            raw_status = status_block
    else:
        awb = payload.get("AWB") or payload.get("waybill")
        raw_status = payload.get("status")

    if not awb or not raw_status:
        logger.warning("[WEBHOOK] Missing AWB or Status, ignoring")
        return {"ok": True}

    # -------------------------
    # 2️⃣ Normalize Status - COMPLETE DELHIVERY STATUS MAPPING
    # -------------------------
    STATUS_MAP = {
        # Forward Shipment Statuses
        "MANIFESTED": "PICKED_UP",              # Shipment created and manifested
        "PICKED UP": "PICKED_UP",               # Picked from warehouse
        "DISPATCHED": "IN_TRANSIT",             # Dispatched from warehouse
        "IN TRANSIT": "IN_TRANSIT",             # In transit to destination
        "REACHED AT DESTINATION HUB": "IN_TRANSIT",  # Reached destination city
        "OUT FOR DELIVERY": "OUT_FOR_DELIVERY", # Out for delivery to customer
        "DELIVERED": "DELIVERED",               # Successfully delivered
        
        # Pickup Statuses
        "OUT FOR PICKUP": "PICKUP_REQUESTED",   # Out to pickup from seller
        "PENDING": "PENDING",                   # Shipment pending
        
        # RTO (Return to Origin) Statuses
        "RTO INITIATED": "RTO",                 # Return initiated
        "RTO IN TRANSIT": "RTO",                # Return in transit
        "RTO OUT FOR DELIVERY": "RTO",          # RTO out for delivery to warehouse
        "RTO DELIVERED": "RTO_DELIVERED",       # Successfully returned to warehouse
        
        # Exception/Failure Statuses
        "DELIVERY FAILED": "FAILED",            # Delivery attempt failed (NDR)
        "UNDELIVERED": "FAILED",                # Could not deliver
        "CANCELLED": "CANCELLED",               # Shipment cancelled
        "LOST": "LOST",                         # Package lost in transit
        "DAMAGED": "DAMAGED",                   # Package damaged
    }


    normalized = raw_status.strip().upper().replace("-", " ")
    internal_status = STATUS_MAP.get(normalized)

    if not internal_status:
        logger.info(f"[WEBHOOK] Unhandled status '{raw_status}', ignored")
        return {"ok": True}

    # -------------------------
    # 2.5️⃣ Status Mapping for Refunds & Exchanges
    # -------------------------
    # Map delivery statuses to refund statuses
    REFUND_STATUS_MAP = {
        'DELIVERED': 'Return Received',
        'FAILED': 'Pickup Failed',
        'RTO_DELIVERED': 'Return Failed - RTO',
        'CANCELLED': 'Cancelled',
        'LOST': 'Lost in Transit',
        'DAMAGED': 'Damaged',
        'PICKED_UP': 'Return In Transit',
        'IN_TRANSIT': 'Return In Transit',
        'OUT_FOR_DELIVERY': 'Delivering to Warehouse',
    }
    
    # Map delivery statuses to exchange return statuses
    EXCHANGE_RETURN_STATUS_MAP = {
        'DELIVERED': 'Return Received',
        'FAILED': 'Pickup Failed',
        'RTO_DELIVERED': 'Return Failed - RTO',
        'CANCELLED': 'Cancelled',
        'LOST': 'Lost in Transit',
        'DAMAGED': 'Damaged',
        'PICKED_UP': 'Return In Transit',
        'IN_TRANSIT': 'Return In Transit',
        'OUT_FOR_DELIVERY': 'Delivering to Warehouse',
    }
    
    # Map delivery statuses to exchange new shipment statuses
    EXCHANGE_NEW_STATUS_MAP = {
        'DELIVERED': 'Completed',
        'FAILED': 'Delivery Failed',
        'RTO': 'RTO In Progress',
        'RTO_DELIVERED': 'RTO Completed',
        'CANCELLED': 'Cancelled',
        'LOST': 'Lost in Transit',
        'DAMAGED': 'Damaged',
        'PICKED_UP': 'Out for Delivery',
        'IN_TRANSIT': 'In Transit',
        'OUT_FOR_DELIVERY': 'Out for Delivery',
    }


    # -------------------------
    # 3️⃣ Find Delivery
    # -------------------------
    delivery = db.query(Delivery).filter(
        Delivery.awb_number == awb
    ).first()

    if not delivery:
        logger.warning(f"[WEBHOOK] No delivery found for AWB {awb}")
        # Continue to check Exchanges, as it might be a return shipment not in Delivery table
    else:
        # -------------------------
        # 4️⃣ Smart Status Progression Validation
        # -------------------------
        # Define status categories
        TERMINAL_STATUSES = ["DELIVERED", "RTO_DELIVERED", "CANCELLED", "LOST"]
        EXCEPTION_STATUSES = ["FAILED", "DAMAGED", "UNDELIVERED"]
        
        # Forward shipment progression
        FORWARD_STATUS_ORDER = [
            "AWB_GENERATED",
            "PICKUP_REQUESTED",
            "PICKED_UP",
            "IN_TRANSIT",
            "OUT_FOR_DELIVERY",
            "DELIVERED",
        ]
        
        # RTO progression
        RTO_STATUS_ORDER = [
            "RTO",
            "RTO_DELIVERED",
        ]
        
        def should_update_status(current_status: str, new_status: str) -> bool:
            """
            Determine if status update should be allowed based on smart category validation
            """
            # Always allow terminal and exception statuses (can happen at any time)
            if new_status in TERMINAL_STATUSES or new_status in EXCEPTION_STATUSES:
                logger.info(f"[WEBHOOK] Allowing terminal/exception status: {new_status}")
                return True
            
            # Don't update if already in terminal state (final states are permanent)
            if current_status in TERMINAL_STATUSES:
                logger.info(f"[WEBHOOK] Blocked update - already in terminal status: {current_status}")
                return False
            
            # Allow transition from forward to RTO (delivery failed, returning to origin)
            if current_status in FORWARD_STATUS_ORDER and new_status in RTO_STATUS_ORDER:
                logger.info(f"[WEBHOOK] Allowing forward → RTO transition: {current_status} → {new_status}")
                return True
            
            # Check forward progression (only allow moving forward, not backward)
            if current_status in FORWARD_STATUS_ORDER and new_status in FORWARD_STATUS_ORDER:
                try:
                    current_index = FORWARD_STATUS_ORDER.index(current_status)
                    new_index = FORWARD_STATUS_ORDER.index(new_status)
                    if new_index >= current_index:
                        return True
                    else:
                        logger.info(f"[WEBHOOK] Blocked backward forward progression: {current_status} → {new_status}")
                        return False
                except ValueError:
                    return True
            
            # Check RTO progression (only allow moving forward in RTO flow)
            if current_status in RTO_STATUS_ORDER and new_status in RTO_STATUS_ORDER:
                try:
                    current_index = RTO_STATUS_ORDER.index(current_status)
                    new_index = RTO_STATUS_ORDER.index(new_status)
                    if new_index >= current_index:
                        return True
                    else:
                        logger.info(f"[WEBHOOK] Blocked backward RTO progression: {current_status} → {new_status}")
                        return False
                except ValueError:
                    return True
            
            # Default: allow update for any other case
            logger.info(f"[WEBHOOK] Allowing status update (default): {current_status} → {new_status}")
            return True
        
        # Validate status transition
        if not should_update_status(delivery.delivery_status, internal_status):
            logger.info(
                f"[WEBHOOK] Ignored invalid status transition {delivery.delivery_status} → {internal_status} for AWB {awb}"
            )
        else:
            # -------------------------
            # 5️⃣ Update DB (Delivery)
            # -------------------------
            delivery.delivery_status = internal_status

            if delivery.order:
                delivery.order.status = internal_status

            db.commit()
            logger.info(f"[WEBHOOK] Updated Delivery AWB {awb} → {internal_status}")

    # -------------------------
    # 6️⃣ Update Exchange (if applicable)
    # -------------------------
    # Check for Exchange Return
    exchange_return = db.query(Exchange).filter(Exchange.return_awb_number == awb).first()
    if exchange_return:
        exchange_return.return_delivery_status = internal_status
        
        # Update exchange return status based on delivery status using dictionary mapping
        if internal_status in EXCHANGE_RETURN_STATUS_MAP:
            exchange_return.status = EXCHANGE_RETURN_STATUS_MAP[internal_status]
            logger.info(f"[WEBHOOK] Updated exchange {exchange_return.id} return status to '{exchange_return.status}'")
            
            # Special handling for critical statuses
            if internal_status == 'DELIVERED':
                logger.info(f"[WEBHOOK] Exchange return delivered to warehouse for exchange {exchange_return.id}")
            elif internal_status in ['FAILED', 'RTO_DELIVERED', 'LOST', 'DAMAGED']:
                logger.warning(f"[WEBHOOK] ⚠️ Exchange {exchange_return.id} return has exception status: {exchange_return.status}")
        
        db.commit()
        logger.info(f"[WEBHOOK] Updated Exchange Return AWB {awb} -> {internal_status}")

    # Check for Exchange New Shipment
    exchange_new = db.query(Exchange).filter(Exchange.new_awb_number == awb).first()
    if exchange_new:
        exchange_new.new_delivery_status = internal_status
        
        # Sync Order Status with Exchange New Delivery Status
        if exchange_new.order:
             exchange_new.order.status = internal_status
             logger.info(f"[WEBHOOK] Synced Order {exchange_new.order_id} status to {internal_status}")

        # Update exchange new status based on delivery status using dictionary mapping
        if internal_status in EXCHANGE_NEW_STATUS_MAP:
            exchange_new.status = EXCHANGE_NEW_STATUS_MAP[internal_status]
            logger.info(f"[WEBHOOK] Updated exchange {exchange_new.id} new shipment status to '{exchange_new.status}'")
            
            # Special handling for completion and critical statuses
            if internal_status == 'DELIVERED':
                exchange_new.completed_at = datetime.utcnow()
                logger.info(f"[WEBHOOK] Exchange {exchange_new.id} completed successfully")
            elif internal_status in ['FAILED', 'RTO', 'RTO_DELIVERED', 'LOST', 'DAMAGED']:
                logger.warning(f"[WEBHOOK] ⚠️ Exchange {exchange_new.id} new shipment has exception status: {exchange_new.status}")
        
        db.commit()
        logger.info(f"[WEBHOOK] Updated Exchange New AWB {awb} -> {internal_status}")

    # -------------------------
    # 7️⃣ Update Refund (if applicable)
    # -------------------------
    # Check for Refund Return Shipment
    refund = db.query(Refund).filter(Refund.return_awb_number == awb).first()
    if refund:
        refund.return_delivery_status = internal_status
        
        # Update refund status based on delivery status using dictionary mapping
        if internal_status in REFUND_STATUS_MAP:
            refund.status = REFUND_STATUS_MAP[internal_status]
            logger.info(f"[WEBHOOK] Updated refund {refund.id} status to '{refund.status}'")
            
            # Special handling for critical statuses
            if internal_status == 'DELIVERED':
                logger.info(f"[WEBHOOK] Refund return delivered to warehouse for refund {refund.id}")
            elif internal_status in ['FAILED', 'RTO_DELIVERED', 'LOST', 'DAMAGED']:
                logger.warning(f"[WEBHOOK] ⚠️ Refund {refund.id} has exception status: {refund.status}")
        
        db.commit()
        logger.info(f"[WEBHOOK] Updated Refund Return AWB {awb} -> {internal_status}")


    return {"ok": True}

<<<<<<< HEAD
=======

# ========================================
# PICKUP SCHEDULING ENDPOINT
# ========================================

@delivery_router.post("/schedule-pickup/{order_id}")
async def schedule_pickup(
    order_id: str,
    pickup_data: dict,
    db: Session = Depends(get_db)
):
    """
    Schedule pickup with Delhivery API
    Integrates with Delhivery's pickup request API
    """
    from app.modules.delivery.delhivery_client import delhivery_client
    from datetime import datetime
    
    logger.info(f"[PICKUP] Scheduling pickup for order {order_id}")
    
    # Get order
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        logger.error(f"[PICKUP] Order not found: {order_id}")
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if AWB is generated
    if not order.awb_number:
        logger.error(f"[PICKUP] AWB not generated for order {order_id}")
        raise HTTPException(
            status_code=400, 
            detail="AWB must be generated before scheduling pickup"
        )
    
    # Extract pickup time and date
    pickup_datetime_str = pickup_data.get("pickup_datetime")
    if not pickup_datetime_str:
        raise HTTPException(status_code=400, detail="pickup_datetime is required")
    
    try:
        # Parse datetime
        pickup_datetime = datetime.fromisoformat(pickup_datetime_str.replace('Z', '+00:00'))
        pickup_date = pickup_datetime.strftime("%Y-%m-%d")
        pickup_time = pickup_datetime.strftime("%H:%M")
        
        logger.info(f"[PICKUP] Parsed date: {pickup_date}, time: {pickup_time}")
        
        # Call Delhivery API
        delhivery_payload = {
            "pickup_time": pickup_time,
            "pickup_date": pickup_date,
            "pickup_location": "sevenxt",  # Must match warehouse name in Delhivery
            "expected_package_count": 1
        }
        
        logger.info(f"[PICKUP] Calling Delhivery API with payload: {delhivery_payload}")
        response = delhivery_client.pickup_request(delhivery_payload)
        logger.info(f"[PICKUP] Delhivery response: {response}")
        
        # Update database
        delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
        if delivery:
            delivery.schedule_pickup = pickup_datetime
            delivery.delivery_status = "PICKUP_REQUESTED"
            logger.info(f"[PICKUP] Updated delivery record for order {order_id}")
        
        order.status = "PICKUP_REQUESTED"
        db.commit()
        
        logger.info(f"[PICKUP] ✅ Pickup scheduled successfully for order {order_id}")
        
        return {
            "success": True,
            "message": "Pickup scheduled successfully",
            "order_id": order_id,
            "pickup_date": pickup_date,
            "pickup_time": pickup_time,
            "delhivery_response": response
        }
        
    except ValueError as e:
        logger.error(f"[PICKUP] Invalid datetime format: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
    except Exception as e:
        logger.exception(f"[PICKUP] Failed to schedule pickup: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to schedule pickup: {str(e)}"
        )

>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
