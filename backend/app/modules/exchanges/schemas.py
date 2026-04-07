from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExchangeCreate(BaseModel):
    order_id: str  # Changed from int - now references orders.order_id (e.g., "ORD-B2C-123")
    
    # New Fields
    order_item_id: Optional[int] = None
    customer: Optional[str] = None
    email: Optional[str] = None
    type: Optional[str] = None

    reason: str
    description: Optional[str] = None
    proof_image_path: Optional[str] = None
    product_id: Optional[str] = None
    product_name: str
    variant_color: Optional[str] = None
    quantity: int = 1
    price: float


class ExchangeResponse(BaseModel):
    id: int
    order_id: str  # String like "ORD-B2C-123"
    
    # New Fields
    order_item_id: Optional[int] = None
    customer: Optional[str] = None
    email: Optional[str] = None
    type: Optional[str] = None
    
    customer_name: Optional[str]
    reason: str
    description: Optional[str]
    proof_image_path: Optional[str]
    product_id: Optional[str] = None
    product_name: str
    variant_color: Optional[str]
    quantity: Optional[int]
    price: Optional[float]
    status: str
    return_awb_number: Optional[str]
    return_label_path: Optional[str]
    return_delivery_status: Optional[str]
    new_awb_number: Optional[str]
    new_label_path: Optional[str]
    new_delivery_status: Optional[str]
    admin_notes: Optional[str]
    quality_approved: Optional[int]
    quality_check_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    approved_at: Optional[datetime]
    quality_checked_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExchangeStatusUpdate(BaseModel):
    status: str
    admin_notes: Optional[str] = None


class QualityCheckRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


class ExchangeRejectRequest(BaseModel):
    rejection_reason: str
