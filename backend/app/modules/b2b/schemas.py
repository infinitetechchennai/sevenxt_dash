# app/modules/b2b/schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Union
from uuid import UUID

class B2BStatusUpdate(BaseModel):
    status: str

class B2BResponse(BaseModel):
    id: UUID
    bussiness_name: str
    gstin: str
    pan: str
    email: str
    phone_number: Union[str, int]
    gst_certificate_url: Optional[str] = None
    business_license_url: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)