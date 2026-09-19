# app/modules/b2b/schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Union
from uuid import UUID

class B2BStatusUpdate(BaseModel):
    status: str

class B2BResponse(BaseModel):
    id: Union[UUID, str]
    bussiness_name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[Union[str, int]] = None
    gst_certificate_url: Optional[str] = None
    business_license_url: Optional[str] = None
    status: Optional[str] = "Pending"
    state: Optional[str] = None
    registration_date: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)