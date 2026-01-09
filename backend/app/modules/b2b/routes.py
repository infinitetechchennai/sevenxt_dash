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

@router.post("/verify-gst")
async def verify_gst(data: VerificationRequest):
    """Verifies GSTIN using Razorpay's modern Identity API"""
    auth = HTTPBasicAuth(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    
    # Standard 2025 Verification Endpoint
    url = "https://api.razorpay.com/v1/instants/gstin"
    
    try:
        response = requests.post(url, json={"gstin": data.number}, auth=auth)
        res_data = response.json()

        print(f"DEBUG GST API RESPONSE: {res_data}")

        if response.status_code == 200:
            return {
                "valid": True,
                "business_name": res_data.get("legal_name", "N/A"),
                "status_desc": f"Active - {res_data.get('status', 'Verified')}"
            }
        else:
            error_msg = res_data.get("error", {}).get("description", "Feature not enabled on your account")
            return {"valid": False, "detail": error_msg}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KYC Gateway Error: {str(e)}")