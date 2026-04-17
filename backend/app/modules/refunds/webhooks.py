from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.modules.refunds.models import Refund
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Delhivery IP Whitelist (from official documentation)
# Production IPs
DELHIVERY_IPS = [
    "13.235.156.68",
    "35.154.208.69",
    "13.127.205.131",
    "13.232.81.51",
    "52.66.71.161",
    "3.6.105.50",
    # Dev/Staging IPs
    "18.138.12.254",
    "52.220.167.45",
    "13.229.106.233",
    "18.141.172.51",
    # Local testing
    "127.0.0.1",
    "localhost",
    "::1"
]

@router.post("/webhooks/delhivery/return")
async def delhivery_return_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint to receive return shipment status updates from Delhivery
    
    Complies with Delhivery SPOC Webhook Requirement document v3.0:
    - Response time < 200ms (uses background tasks)
    - Handles both simple and detailed payload formats
    - IP whitelisting for security
    - Parses scans array for detailed tracking
    """
    try:
        # ✅ FIX #3: IP Whitelisting (Security)
        client_ip = request.client.host
        if client_ip not in DELHIVERY_IPS:
            logger.warning(f"[WEBHOOK] ⚠️ Unauthorized IP: {client_ip}")
            raise HTTPException(status_code=403, detail="Forbidden")
        
        # ⏱️ Fast operations only (< 200ms total)
        payload = await request.json()
        logger.info(f"[WEBHOOK] Received from {client_ip}: {payload}")
        
        # Extract waybill (supports both field names)
        waybill = payload.get('waybill') or payload.get('awb')
        
        # ✅ FIX #1: Extract status from multiple sources (handles both formats)
        status = payload.get('status') or payload.get('Status')
        
        # Check scans array if status not in root (detailed payload format)
        if not status and 'scans' in payload:
            scans = payload.get('scans', [])
            if scans and len(scans) > 0:
                # Get the latest scan (last item in array)
                latest_scan = scans[-1]
                scan_detail = latest_scan.get('ScanDetail', {})
                # Try different field names
                status = (scan_detail.get('Scan') or 
                         scan_detail.get('Status') or 
                         scan_detail.get('ScanType'))
                logger.info(f"[WEBHOOK] Extracted status from scans array: {status}")
        
        # Quick validation
        if not waybill:
            logger.error("[WEBHOOK] No waybill found in payload")
            return {"status": "error", "message": "No waybill in payload"}
        
        if not status:
            logger.error("[WEBHOOK] No status found in payload")
            return {"status": "error", "message": "No status in payload"}
        
        # ✅ FIX #2: Process in background to respond < 200ms
        background_tasks.add_task(
            process_refund_webhook,
            waybill,
            status,
            payload
        )
        
        # ⏱️ Return immediately (< 200ms as per Delhivery documentation)
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[WEBHOOK] Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}


def process_refund_webhook(waybill: str, status: str, payload: dict):
    """
    Background task to update database
    Runs after webhook response is sent (no 200ms time limit)
    """
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        logger.info(f"[WEBHOOK] Processing AWB: {waybill}, Status: {status}")
        
        # Find refund by return AWB number
        refund = db.query(Refund).filter(
            Refund.return_awb_number == waybill
        ).first()
        
        if not refund:
            logger.warning(f"[WEBHOOK] No refund found for return AWB: {waybill}")
            return
        
        # Update return delivery status
        old_status = refund.return_delivery_status
        refund.return_delivery_status = status
        
        logger.info(f"[WEBHOOK] Updating refund {refund.id} return status: {old_status} → {status}")
        
        # Handle specific statuses
        status_lower = status.lower().replace(" ", "").replace("_", "")
        
        if status_lower in ['delivered', 'dlvd', 'dl']:
            logger.info(f"[WEBHOOK] ✅ Return package delivered to warehouse for refund {refund.id}")
            # TODO: Send notification to admin to verify product and mark as Completed
            # You can add email notification or in-app notification here
        
        elif status_lower in ['pickedup', 'pickup', 'pu']:
            logger.info(f"[WEBHOOK] 📦 Package picked up from customer for refund {refund.id}")
        
        elif status_lower in ['intransit', 'transit', 'it']:
            logger.info(f"[WEBHOOK] 🚚 Package in transit for refund {refund.id}")
        
        elif status_lower in ['undelivered', 'ud', 'failed']:
            logger.warning(f"[WEBHOOK] ⚠️ Delivery attempt failed for refund {refund.id}")
        
        elif status_lower in ['rto', 'returntoorigin']:
            logger.warning(f"[WEBHOOK] ⚠️ Package returning to origin for refund {refund.id}")
        
        # Commit changes to database
        try:
            db.add(refund)  # Explicitly add to session
            db.flush()      # Flush to ensure changes are staged
            db.commit()     # Commit to database
            logger.info(f"[WEBHOOK] ✅ Database updated successfully for refund {refund.id}")
        except Exception as commit_error:
            db.rollback()
            logger.error(f"[WEBHOOK] ❌ Database commit failed: {commit_error}")
            raise Exception(f"Failed to update database: {commit_error}")
        
        # Verify the update
        db.refresh(refund)
        logger.info(f"[WEBHOOK] Verified status in DB: {refund.return_delivery_status}")
        
    except Exception as e:
        logger.exception(f"[WEBHOOK] Error updating database: {e}")
        db.rollback()
    finally:
        db.close()


@router.get("/webhooks/test")
async def test_webhook():
    """Test endpoint to verify webhook is accessible"""
    return {
        "status": "ok",
        "message": "Webhook endpoint is working",
        "version": "2.0 - Optimized with background tasks"
    }
