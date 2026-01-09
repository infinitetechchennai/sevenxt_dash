"""
Webhook Security Module
Handles authentication and verification of incoming webhooks from Delhivery
"""

import hmac
import hashlib
import logging
from typing import Optional
from fastapi import Header, HTTPException, Request
import json

logger = logging.getLogger(__name__)


class WebhookSecurityManager:
    """Manages webhook authentication and verification"""
    
    def __init__(self, webhook_secret: Optional[str] = None):
        """
        Initialize webhook security manager
        
        Args:
            webhook_secret: Secret key shared with Delhivery for signature verification
                          If None, signature verification will be skipped (NOT RECOMMENDED for production)
        """
        self.webhook_secret = webhook_secret
        self.enabled = webhook_secret is not None
        
        if not self.enabled:
            logger.warning("⚠️ Webhook signature verification is DISABLED. This is insecure for production!")
    
    
    def generate_signature(self, payload: dict) -> str:
        """
        Generate HMAC SHA256 signature for webhook payload
        
        Args:
            payload: Webhook payload dictionary
            
        Returns:
            Hex-encoded signature string
        """
        if not self.webhook_secret:
            return ""
        
        # Convert payload to JSON string (sorted keys for consistency)
        payload_string = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        
        # Generate HMAC SHA256 signature
        signature = hmac.new(
            key=self.webhook_secret.encode('utf-8'),
            msg=payload_string.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return signature
    
    
    def verify_signature(self, payload: dict, received_signature: str) -> bool:
        """
        Verify webhook signature using constant-time comparison
        
        Args:
            payload: Webhook payload dictionary
            received_signature: Signature received in webhook headers
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.enabled:
            logger.warning("⚠️ Signature verification skipped (disabled)")
            return True
        
        if not received_signature:
            logger.error("❌ No signature provided in webhook request")
            return False
        
        # Generate expected signature
        expected_signature = self.generate_signature(payload)
        
        # Use constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(expected_signature, received_signature)
        
        if is_valid:
            logger.info("✅ Webhook signature verified successfully")
        else:
            logger.error(f"❌ Webhook signature verification FAILED!")
            logger.error(f"   Expected: {expected_signature[:20]}...")
            logger.error(f"   Received: {received_signature[:20]}...")
        
        return is_valid
    
    
    async def verify_webhook_request(
        self,
        request: Request,
        x_delhivery_signature: Optional[str] = Header(None),
        x_webhook_signature: Optional[str] = Header(None),
        x_signature: Optional[str] = Header(None)
    ) -> dict:
        """
        Verify incoming webhook request
        
        Checks multiple possible signature header names:
        - X-Delhivery-Signature
        - X-Webhook-Signature
        - X-Signature
        
        Args:
            request: FastAPI Request object
            x_delhivery_signature: Signature from X-Delhivery-Signature header
            x_webhook_signature: Signature from X-Webhook-Signature header
            x_signature: Signature from X-Signature header
            
        Returns:
            Webhook payload dictionary if verification succeeds
            
        Raises:
            HTTPException: If signature verification fails
        """
        # Get request body
        body = await request.body()
        
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error("❌ Invalid JSON in webhook request")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # If signature verification is disabled, return payload
        if not self.enabled:
            logger.warning("⚠️ Processing webhook without signature verification (INSECURE)")
            return payload
        
        # Try to get signature from different possible headers
        signature = x_delhivery_signature or x_webhook_signature or x_signature
        
        if not signature:
            logger.error("❌ No signature found in webhook headers")
            logger.error(f"   Checked headers: X-Delhivery-Signature, X-Webhook-Signature, X-Signature")
            raise HTTPException(
                status_code=401,
                detail="Missing webhook signature. Request rejected for security."
            )
        
        # Verify signature
        if not self.verify_signature(payload, signature):
            logger.error("❌ Webhook signature verification FAILED - Possible attack or misconfiguration!")
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature. Request rejected."
            )
        
        logger.info("✅ Webhook request verified successfully")
        return payload


# Alternative: IP Whitelist-based authentication
class IPWhitelistManager:
    """
    Alternative/Additional security: Verify webhook requests come from Delhivery IPs
    """
    
    # Delhivery's known IP ranges (you need to get these from Delhivery support)
    DELHIVERY_IPS = [
        "103.242.124.0/24",  # Example - replace with actual Delhivery IPs
        "103.242.125.0/24",  # Example
        # Add more IP ranges as provided by Delhivery
    ]
    
    @staticmethod
    def is_ip_whitelisted(client_ip: str) -> bool:
        """
        Check if client IP is in Delhivery's whitelist
        
        Args:
            client_ip: Client IP address
            
        Returns:
            True if IP is whitelisted, False otherwise
        """
        # Simple implementation - for production, use ipaddress module for CIDR matching
        for allowed_ip_range in IPWhitelistManager.DELHIVERY_IPS:
            if client_ip.startswith(allowed_ip_range.split('/')[0][:10]):
                return True
        return False
    
    @staticmethod
    async def verify_ip(request: Request):
        """
        Verify webhook request comes from whitelisted IP
        
        Args:
            request: FastAPI Request object
            
        Raises:
            HTTPException: If IP is not whitelisted
        """
        client_ip = request.client.host
        
        if not IPWhitelistManager.is_ip_whitelisted(client_ip):
            logger.error(f"❌ Webhook request from non-whitelisted IP: {client_ip}")
            raise HTTPException(
                status_code=403,
                detail="Request from unauthorized IP address"
            )
        
        logger.info(f"✅ Webhook request from whitelisted IP: {client_ip}")


# Simple API Key authentication (fallback option)
class APIKeyAuth:
    """
    Simple API key authentication for webhooks
    Use this if Delhivery doesn't support HMAC signatures
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.enabled = api_key is not None
    
    async def verify_api_key(
        self,
        x_api_key: Optional[str] = Header(None),
        authorization: Optional[str] = Header(None)
    ):
        """
        Verify API key from headers
        
        Args:
            x_api_key: API key from X-API-Key header
            authorization: API key from Authorization header
            
        Raises:
            HTTPException: If API key is invalid
        """
        if not self.enabled:
            return
        
        # Try to get API key from different headers
        provided_key = x_api_key
        
        # Also check Authorization header (format: "Bearer <key>")
        if not provided_key and authorization:
            if authorization.startswith("Bearer "):
                provided_key = authorization[7:]
        
        if not provided_key:
            logger.error("❌ No API key provided in webhook request")
            raise HTTPException(status_code=401, detail="Missing API key")
        
        if provided_key != self.api_key:
            logger.error("❌ Invalid API key in webhook request")
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        logger.info("✅ API key verified successfully")
