from pydantic import BaseModel, field_validator
from datetime import date
from typing import Optional

class CouponCreate(BaseModel):
    code: str
    type: str
    value: str
    target: str
    expiry: Optional[date] = None
    min_order_value: Optional[str] = "0"
    usage_limit: Optional[str] = "100"

    # Fix for empty strings from frontend
    @field_validator('expiry', mode='before')
    def parse_expiry(cls, v):
        if v == "" or v is None:
            return None
        return v

class CouponUpdate(BaseModel):
    code: Optional[str] = None
    type: Optional[str] = None
    value: Optional[str] = None
    target: Optional[str] = None
    expiry: Optional[date] = None
    min_order_value: Optional[str] = None
    usage_limit: Optional[str] = None

class CouponOut(BaseModel):
    id: int
    code: str
    type: str
    value: str
    target: str
    usage_count: str
    status: str
    expiry: Optional[date] = None
    min_order_value: Optional[str] = "0"
    usage_limit: Optional[str] = "100"
    razorpay_offer_id: Optional[str] = None

    class Config:
        from_attributes = True