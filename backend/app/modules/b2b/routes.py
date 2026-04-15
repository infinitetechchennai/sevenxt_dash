from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import requests
from requests.auth import HTTPBasicAuth
from pydantic import BaseModel
from uuid import UUID

from app.database import get_db
from app.config import settings
from . import service, schemas

# We use prefix="/b2b" so it appends to the main.py prefix ("/api/v1")
# Resulting URL: /api/v1/b2b/...
router = APIRouter(prefix="/b2b", tags=["B2B Management"])

# --- SCHEMA FOR AUTO-VERIFICATION REQUEST ---
class VerificationRequest(BaseModel):
    number: str

# 1. FETCH ALL USERS (Fixed routing)
@router.get("/users", response_model=List[schemas.B2BResponse])
def read_b2b_users(db: Session = Depends(get_db)):
    """
    Fetches all B2B records.
    Called from frontend: /api/v1/b2b/users
    """
    users = service.get_b2b_users(db)
    return users

# 2. UPDATE STATUS (Existing workflow)
@router.put("/verify/{id}", response_model=schemas.B2BResponse)
def verify_b2b_user(id: UUID, status_update: schemas.B2BStatusUpdate, db: Session = Depends(get_db)):
    updated_user = service.update_status(db, id, status_update.status)
    if not updated_user:
        raise HTTPException(status_code=404, detail="B2B Application not found")
    return updated_user

# ---------------------------------------------------------
# UPDATED: RAZORPAY 2025 INSTANT VERIFICATION WORKFLOW
# ---------------------------------------------------------

@router.post("/verify-pan")
async def verify_pan(data: VerificationRequest):
    """Verifies PAN card using Razorpay's modern Identity API"""
    auth = HTTPBasicAuth(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    
    # Standard 2025 Verification Endpoint
    url = "https://api.razorpay.com/v1/instants/pan"
    
    try:
        response = requests.post(url, json={"pan": data.number}, auth=auth)
        res_data = response.json()
        
        # This print shows the real error in your terminal
        print(f"DEBUG PAN API RESPONSE: {res_data}")

        if response.status_code == 200:
            return {
                "valid": True,
                "business_name": res_data.get("name", "N/A"),
                "status_desc": "Authentic Document"
            }
        else:
            error_msg = res_data.get("error", {}).get("description", "Verification feature not enabled")
            return {"valid": False, "detail": error_msg}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KYC Gateway Error: {str(e)}")

import re

@router.post("/verify-gst")
async def verify_gst(data: VerificationRequest):
    """Verifies GSTIN using Sandbox API via two-step auth"""
    
    gstin = (data.number or "").strip().upper()

    # 1. Validate GSTIN format using regex
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    if not re.match(pattern, gstin):
        return {"valid": False, "detail": "Invalid GSTIN format"}

    try:
        # 2a. Authenticate with Sandbox to get Bearer token
        auth_url = "https://api.sandbox.co.in/authenticate"
        auth_headers = {
            "x-api-key": settings.SANDBOX_API_KEY,
            "x-api-secret": settings.SANDBOX_API_SECRET,
            "x-api-version": "1.0",
            "accept": "application/json"
        }
        
        auth_response = requests.post(auth_url, headers=auth_headers)
        auth_data = auth_response.json()
        
        if auth_response.status_code != 200 or "access_token" not in auth_data:
            print(f"DEBUG SANDBOX AUTH FAILED: {auth_data}")
            return {"valid": False, "detail": "Sandbox Authentication Failed. Please check API keys."}
            
        access_token = auth_data["access_token"]

        # 2b. Call Sandbox API to verify GSTIN
        url = f"https://api.sandbox.co.in/gsp/taxpayer/gstin/{gstin}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "x-api-key": settings.SANDBOX_API_KEY,
            "x-api-version": "1.0",
            "accept": "application/json"
        }

        response = requests.get(url, headers=headers)
        res_data = response.json()

        print(f"DEBUG GST API RESPONSE: {res_data}")
        
        # Sandbox wraps the successful response under "data"
        api_data = res_data.get("data", {})
        status = api_data.get("sts", "")

        # 3. Check response
        if response.status_code == 200 and status == "Active":
            legal_name = api_data.get("lgnm", "")
            trade_name = api_data.get("tradeNam", "")
            reg_date = api_data.get("rgdt", "")
            
            # Extract state code
            state_code = api_data.get("pradr", {}).get("addr", {}).get("stcd", "N/A")
            
            return {
                "valid": True,
                "business_name": trade_name or legal_name or "N/A",
                "status_desc": "Active",
                "state": state_code,
                "registration_date": reg_date
            }
        else:
            error_msg = res_data.get("message", "GSTIN is not Active or not found")
            return {"valid": False, "detail": f"Verification failed: {error_msg}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KYC Gateway Error: {str(e)}")