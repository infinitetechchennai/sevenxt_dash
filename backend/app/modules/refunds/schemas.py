from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class RefundBase(BaseModel):
    order_id: int
    reason: str
    amount: float
    proof_image_path: Optional[str] = None

class RefundCreate(RefundBase):
    pass

class RefundStatusUpdate(BaseModel):
    status: str  # Pending, Approved, Rejected, Completed

class RefundAWBUpdate(BaseModel):
    return_awb_number: str
    return_label_path: str

class RefundReject(BaseModel):
    rejection_reason: str
    admin_notes: Optional[str] = None

class RefundResponse(BaseModel):
    id: int
    order_id: int
    order_number: Optional[str] = None  # From orders.order_id
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    products: Optional[Any] = None  # Changed from str to Any to handle JSON
    
    reason: str
    amount: float
    status: str
    proof_image_path: Optional[str] = None
    return_awb_number: Optional[str] = None
    return_label_path: Optional[str] = None
    return_delivery_status: Optional[str] = None  # Delhivery tracking status
    
    # Rejection details
    rejection_reason: Optional[str] = None
    admin_notes: Optional[str] = None
    
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    approved_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        orm_mode = True
