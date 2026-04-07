"""
Example: Secured Delhivery Webhook Endpoint
Shows how to integrate webhook security into your existing webhook
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.modules.exchanges.webhook_security import WebhookSecurityManager, APIKeyAuth
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exchanges", tags=["Exchange Webhooks - Secured"])

# Initialize security manager
webhook_security = WebhookSecurityManager(
    webhook_secret=settings.DELHIVERY_WEBHOOK_SECRET if settings.WEBHOOK_SIGNATURE_VERIFICATION_ENABLED else None
)

# Alternative: API Key authentication (simpler, but less secure)
api_key_auth = APIKeyAuth(api_key=settings.DELHIVERY_WEBHOOK_SECRET)


# ============================================
# OPTION 1: HMAC Signature Verification (RECOMMENDED)
# ============================================

@router.post("/webhook/delhivery-secure")
async def delhivery_webhook_secure(
    request: Request,
    db: Session = Depends(get_db),
    x_delhivery_signature: Optional[str] = Header(None),
    x_webhook_signature: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None)
):
    """
    Secured Delhivery webhook endpoint with HMAC signature verification
    
    Security Features:
    - HMAC SHA256 signature verification
    - Constant-time comparison to prevent timing attacks
    - Multiple signature header support
    
    Headers Expected:
    - X-Delhivery-Signature: HMAC SHA256 signature of the payload
    OR
    - X-Webhook-Signature: Alternative signature header
    OR
    - X-Signature: Fallback signature header
    
    Example Delhivery Request:
    POST /api/v1/exchanges/webhook/delhivery-secure
    Headers:
        X-Delhivery-Signature: abc123def456...
        Content-Type: application/json
    Body:
        {
            "waybill": "AWB123",
            "status": "Delivered",
            "scans": [...]
        }
    """
    try:
        # Verify webhook signature and get payload
        webhook_data = await webhook_security.verify_webhook_request(
            request=request,
            x_delhivery_signature=x_delhivery_signature,
            x_webhook_signature=x_webhook_signature,
            x_signature=x_signature
        )
        
        logger.info(f"✅ Secured webhook request verified for AWB: {webhook_data.get('waybill')}")
        
        # Process webhook (your existing logic)
        # ... (copy your existing webhook processing code here)
        
        return {
            "success": True,
            "message": "Secured webhook processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing secured webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# OPTION 2: API Key Authentication (SIMPLER)
# ============================================

@router.post("/webhook/delhivery-apikey")
async def delhivery_webhook_apikey(
    webhook_data: dict,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    """
    Delhivery webhook with simple API key authentication
    
    Headers Expected:
    - X-API-Key: your-secret-api-key
    OR
    - Authorization: Bearer your-secret-api-key
    
    Example Request:
    POST /api/v1/exchanges/webhook/delhivery-apikey
    Headers:
        X-API-Key: your-delhivery-webhook-secret-change-in-production
        Content-Type: application/json
    Body:
        {
            "waybill": "AWB123",
            "status": "Delivered"
        }
    """
    try:
        # Verify API key
        await api_key_auth.verify_api_key(
            x_api_key=x_api_key,
            authorization=authorization
        )
        
        logger.info(f"✅ API key verified for webhook: {webhook_data.get('waybill')}")
        
        # Process webhook (your existing logic)
        # ... (copy your existing webhook processing code here)
        
        return {
            "success": True,
            "message": "API key authenticated webhook processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# OPTION 3: Combined Security (MOST SECURE)
# ============================================

@router.post("/webhook/delhivery-ultra-secure")
async def delhivery_webhook_ultra_secure(
    request: Request,
    db: Session = Depends(get_db),
    x_delhivery_signature: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
):
    """
    Ultra-secure webhook with both signature verification AND API key
    
    Security Layers:
    1. API Key verification
    2. HMAC signature verification
    3. IP whitelist (optional - uncomment to enable)
    
    Headers Expected:
    - X-API-Key: your-secret-api-key
    - X-Delhivery-Signature: HMAC SHA256 signature
    """
    try:
        # Layer 1: Verify API key
        await api_key_auth.verify_api_key(x_api_key=x_api_key)
        logger.info("✅ Layer 1: API key verified")
        
        # Layer 2: Verify HMAC signature
        webhook_data = await webhook_security.verify_webhook_request(
            request=request,
            x_delhivery_signature=x_delhivery_signature
        )
        logger.info("✅ Layer 2: Signature verified")
        
        # Layer 3: IP Whitelist (optional - uncomment to enable)
        # from app.modules.exchanges.webhook_security import IPWhitelistManager
        # await IPWhitelistManager.verify_ip(request)
        # logger.info("✅ Layer 3: IP whitelisted")
        
        logger.info(f"✅ Ultra-secure webhook verified for AWB: {webhook_data.get('waybill')}")
        
        # Process webhook (your existing logic)
        # ... (copy your existing webhook processing code here)
        
        return {
            "success": True,
            "message": "Ultra-secure webhook processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing ultra-secure webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
