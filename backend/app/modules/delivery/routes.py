from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.modules.orders.models import Delivery, Order
from app.modules.exchanges.models import Exchange
from app.modules.refunds.models import Refund
from datetime import datetime
import logging
import json

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)

# Add delivery router for pickup scheduling
delivery_router = APIRouter(prefix="/delivery", tags=["Delivery"])

def process_delhivery_update_task(payload: dict):
    """
    Background task to process Delhivery webhook updates.
    Runs asynchronously after the 200 OK response is sent.
    """
    db = SessionLocal()
    try:
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
            logger.warning("[WEBHOOK-BG] Missing AWB or Status in payload, ignoring")
            return

        # -------------------------
        # 2️⃣ Normalize Status - COMPLETE DELHIVERY STATUS MAPPING
        # -------------------------
        STATUS_MAP = {
            # Initial Statuses
            "SHIPMENT CREATED": "AWB_GENERATED",        # Initial status after AWB generation
            "MANIFESTED": "PICKED_UP",                  # Shipment created and manifested
            "READY FOR PICKUP": "PICKUP_REQUESTED",     # Shipment ready for courier pickup
            
            # Pickup Statuses
            "OUT FOR PICKUP": "PICKUP_REQUESTED",       # Out to pickup from seller
            "PICKED UP": "PICKED_UP",                   # Picked from warehouse
            "PICKUP EXCEPTION": "PICKUP_FAILED",        # Pickup failed
            "PICKUP RESCHEDULED": "PICKUP_REQUESTED",   # Pickup rescheduled (mapped to requested to keep it active)
            "PENDING": "PENDING",                       # Shipment pending
            
            # Transit Statuses
            "DISPATCHED": "IN_TRANSIT",                 # Dispatched from warehouse
            "IN TRANSIT": "IN_TRANSIT",                 # In transit to destination
            "REACHED AT DESTINATION HUB": "IN_TRANSIT", # Reached destination city
            "SHIPMENT DELAYED": "IN_TRANSIT",           # Delay in transit
            "SHIPMENT HELD": "IN_TRANSIT",              # Held at customs/hub
            
            # Delivery Statuses
            "OUT FOR DELIVERY": "OUT_FOR_DELIVERY",     # Out for delivery to customer
            "DELIVERED": "DELIVERED",                   # Successfully delivered
            "PARTIAL DELIVERED": "DELIVERED",           # Some items delivered (multi-piece)
            "DELIVERY EXCEPTION": "FAILED",             # Delivery issue
            "DELIVERY RESCHEDULED": "OUT_FOR_DELIVERY", # Delivery rescheduled
            
            # Failure Statuses
            "DELIVERY FAILED": "FAILED",                # Delivery attempt failed (NDR)
            "UNDELIVERED": "FAILED",                    # Could not deliver
            
            # RTO (Return to Origin) Statuses
            "RTO INITIATED": "RTO",                     # Return initiated
            "RTO IN TRANSIT": "RTO",                    # Return in transit
            "RTO OUT FOR DELIVERY": "RTO",              # RTO out for delivery to warehouse
            "RTO DELIVERED": "RTO_DELIVERED",           # Successfully returned to warehouse
            
            # Exception Statuses
            "CANCELLED": "CANCELLED",                   # Shipment cancelled
            "LOST": "LOST",                             # Package lost in transit
            "DAMAGED": "DAMAGED",                       # Package damaged
            "SHIPMENT DESTROYED": "DESTROYED",          # Package destroyed
        }

        normalized = raw_status.strip().upper().replace("-", " ")
        internal_status = STATUS_MAP.get(normalized)

        if not internal_status:
            logger.info(f"[WEBHOOK-BG] Unhandled status '{raw_status}', ignored")
            return

        # -------------------------
        # 2.5️⃣ Status Mapping for Refunds & Exchanges
        # -------------------------
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
        delivery = db.query(Delivery).filter(Delivery.awb_number == awb).first()

        if delivery:
            # -------------------------
            # 4️⃣ Smart Status Progression Validation
            # -------------------------
            def should_update_status(current_status: str, new_status: str) -> bool:
                """Determine if status update should be allowed based on smart category validation"""
                TERMINAL_STATUSES = ["DELIVERED", "RTO_DELIVERED", "CANCELLED", "LOST"]
                EXCEPTION_STATUSES = ["FAILED", "DAMAGED", "UNDELIVERED"]
                
                # Forward shipment progression
                FORWARD_STATUS_ORDER = [
                    "AWB_GENERATED", "PICKUP_REQUESTED", "PICKED_UP", 
                    "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED"
                ]
                
                # RTO progression
                RTO_STATUS_ORDER = ["RTO", "RTO_DELIVERED"]

                if new_status in TERMINAL_STATUSES or new_status in EXCEPTION_STATUSES:
                    return True
                
                if current_status in TERMINAL_STATUSES:
                    return False
                
                if current_status in FORWARD_STATUS_ORDER and new_status in RTO_STATUS_ORDER:
                    return True
                
                if current_status in FORWARD_STATUS_ORDER and new_status in FORWARD_STATUS_ORDER:
                    try:
                        current_index = FORWARD_STATUS_ORDER.index(current_status)
                        new_index = FORWARD_STATUS_ORDER.index(new_status)
                        return new_index >= current_index
                    except ValueError:
                        return True
                
                if current_status in RTO_STATUS_ORDER and new_status in RTO_STATUS_ORDER:
                    try:
                        current_index = RTO_STATUS_ORDER.index(current_status)
                        new_index = RTO_STATUS_ORDER.index(new_status)
                        return new_index >= current_index
                    except ValueError:
                        return True
                
                return True

            if not should_update_status(delivery.delivery_status, internal_status):
                logger.info(f"[WEBHOOK-BG] Ignored invalid transition {delivery.delivery_status} → {internal_status} for AWB {awb}")
            else:
                # -------------------------
                # 5️⃣ Update DB (Delivery)
                # -------------------------
                delivery.delivery_status = internal_status
                if delivery.order:
                    delivery.order.status = internal_status
                db.commit()
                logger.info(f"[WEBHOOK-BG] Updated Delivery AWB {awb} → {internal_status}")

        # -------------------------
        # 6️⃣ Update Exchange (if applicable)
        # -------------------------
        exchange_return = db.query(Exchange).filter(Exchange.return_awb_number == awb).first()
        if exchange_return:
            if not delivery: # Only update status if not main delivery (or sync logic)
                 pass # Logic handled below

            exchange_return.return_delivery_status = internal_status
            if internal_status in EXCHANGE_RETURN_STATUS_MAP:
                exchange_return.status = EXCHANGE_RETURN_STATUS_MAP[internal_status]
            db.commit()
            logger.info(f"[WEBHOOK-BG] Updated Exchange Return AWB {awb} -> {internal_status}")

        exchange_new = db.query(Exchange).filter(Exchange.new_awb_number == awb).first()
        if exchange_new:
            exchange_new.new_delivery_status = internal_status
            if exchange_new.order:
                 exchange_new.order.status = internal_status
            
            if internal_status in EXCHANGE_NEW_STATUS_MAP:
                exchange_new.status = EXCHANGE_NEW_STATUS_MAP[internal_status]
                if internal_status == 'DELIVERED':
                    exchange_new.completed_at = datetime.utcnow()
            db.commit()
            logger.info(f"[WEBHOOK-BG] Updated Exchange New AWB {awb} -> {internal_status}")

        # -------------------------
        # 7️⃣ Update Refund (if applicable)
        # -------------------------
        refund = db.query(Refund).filter(Refund.return_awb_number == awb).first()
        if refund:
            refund.return_delivery_status = internal_status
            if internal_status in REFUND_STATUS_MAP:
                refund.status = REFUND_STATUS_MAP[internal_status]
            db.commit()
            logger.info(f"[WEBHOOK-BG] Updated Refund Return AWB {awb} -> {internal_status}")

    except Exception as e:
        logger.error(f"[WEBHOOK-BG] Error processing webhook for AWB {payload.get('Shipment', {}).get('AWB')}: {e}")
        db.rollback()
    finally:
        db.close()


@router.post("/delhivery")
async def delhivery_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Production-safe Delhivery Webhook Handler.
    Handles Pickup → In-Transit → Delivered updates asynchronously.
    """
    from app.config import settings
    import hmac
    import hashlib
    
    # ========================================
    # SECURITY LAYER 1: IP Whitelisting
    # ========================================
    client_ip = request.client.host if request.client else "unknown"
    
    if settings.WEBHOOK_ALLOWED_IPS and client_ip not in settings.WEBHOOK_ALLOWED_IPS:
        logger.warning(f"[WEBHOOK] ❌ Blocked request from unauthorized IP: {client_ip}")
        raise HTTPException(status_code=403, detail="Unauthorized IP address")
    
    # ========================================
    # SECURITY LAYER 2: Signature Verification
    # ========================================
    if settings.WEBHOOK_SIGNATURE_VERIFICATION_ENABLED:
        signature = request.headers.get("X-Delhivery-Signature") or request.headers.get("X-Webhook-Signature")
        if not signature:
            logger.warning("[WEBHOOK] ❌ Missing webhook signature")
            raise HTTPException(status_code=401, detail="Missing webhook signature")
        
        body = await request.body()
        expected_signature = hmac.new(
            settings.DELHIVERY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("[WEBHOOK] ❌ Invalid signature")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        payload = json.loads(body.decode())
    else:
        payload = await request.json()
    
    # ========================================
    # SECURITY LAYER 3: Background Processing
    # ========================================
    # Return 200 OK immediately and process in background
    logger.info(f"[WEBHOOK] Payload received from {client_ip} - Queuing background task")
    background_tasks.add_task(process_delhivery_update_task, payload)
    
    return {"ok": True}

# ========================================
# TEST ENDPOINT
# ========================================
@delivery_router.get("/test")
async def test_delivery_router():
    """Test endpoint to verify delivery_router is working"""
    return {"message": "Delivery router is working!", "status": "ok"}

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
    Schedule pickup for an order.
    1. Saves pickup time to DB
    2. Calls Delhivery Pickup Request API: POST /fm/request/new/

    Body:
    {
        "pickup_datetime": "2026-02-26T15:00:00",   (ISO format)
        "expected_package_count": 1                  (optional, default 1)
    }
    """
    try:
        pickup_datetime = pickup_data.get("pickup_datetime")
        expected_package_count = pickup_data.get("expected_package_count", 1)

        if not pickup_datetime:
            raise HTTPException(status_code=400, detail="pickup_datetime is required")

        # Find the order
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

        # Find the delivery
        delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
        if not delivery:
            raise HTTPException(status_code=404, detail=f"Delivery not found for order {order_id}")

        # --- Validate AWB exists before scheduling pickup ---
        if not delivery.awb_number:
            raise HTTPException(
                status_code=400,
                detail="AWB not generated yet. Generate AWB before scheduling pickup."
            )

        # Parse the datetime
        try:
            pickup_dt = datetime.fromisoformat(pickup_datetime.replace('Z', '+00:00'))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")

        # Format for Delhivery API (as per docs)
        pickup_date_str = pickup_dt.strftime("%Y-%m-%d")   # "2026-02-26"
        pickup_time_str = pickup_dt.strftime("%H:%M:%S")   # "15:00:00"

        # ─────────────────────────────────────────────────────────
        # STEP 1: Save pickup time to YOUR DB first (always)
        # ─────────────────────────────────────────────────────────
        delivery.schedule_pickup = pickup_dt
        delivery.delivery_status = "Pickup Time Scheduled"
        order.status = "Pickup Time Scheduled"
        db.commit()
        db.refresh(delivery)

        logger.info(f"✅ Pickup saved in DB for order {order_id} at {pickup_date_str} {pickup_time_str}")

        # ─────────────────────────────────────────────────────────
        # STEP 2: Call Delhivery Pickup Request API
        # POST /fm/request/new/
        # Body: pickup_time, pickup_date, pickup_location, expected_package_count
        # ─────────────────────────────────────────────────────────
        delhivery_pickup_result = None
        delhivery_error = None

        try:
            from app.modules.delivery.delhivery_client import DelhiveryClient
            from app.modules.delivery.shipment_service import DELHIVERY_TOKEN

            client = DelhiveryClient(token=DELHIVERY_TOKEN, is_production=False)

            delhivery_pickup_result = client.request_pickup(
                pickup_date=pickup_date_str,
                pickup_time=pickup_time_str,
                pickup_location="sevenxt",          # Your registered warehouse name
                expected_package_count=int(expected_package_count),
            )

            logger.info(f"[PICKUP REQUEST] Delhivery Response: {delhivery_pickup_result}")

        except Exception as deli_err:
            # Don't fail the whole request if Delhivery API fails
            # DB is already updated
            delhivery_error = str(deli_err)
            logger.error(f"❌ Delhivery Pickup API failed for {order_id}: {deli_err}")

        # ─────────────────────────────────────────────────────────
        # STEP 3: Return response
        # ─────────────────────────────────────────────────────────
        response_data = {
            "success": True,
            "message": "Pickup scheduled successfully",
            "order_id": order_id,
            "pickup_date": pickup_date_str,
            "pickup_time": pickup_time_str,
            "delivery_status": delivery.delivery_status,
            "delhivery_pickup_response": delhivery_pickup_result,
        }

        if delhivery_error:
            response_data["delhivery_warning"] = f"DB updated but Delhivery API call failed: {delhivery_error}"

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error scheduling pickup for order {order_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

