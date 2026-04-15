from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class OrderBase(BaseModel):
    order_id : str
    order_number: Optional[str] = None
    gst_type: Optional[str] = None
    seller_gstin: Optional[str] = None
    igst_percentage: Optional[float] = 0.0
    customer_type: Optional[str] = None
    customer_name: Optional[str] = None  # Added direct field
    user_id: Optional[int] = None
    products: Optional[Any] = None # JSON string
    amount: Optional[float] = None
    payment: Optional[str] = None
    status: Optional[str] = None
    awb_number: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    breadth: Optional[float] = None
    length: Optional[float] = None
    
    # GST Percentages
    sgst_percentage: Optional[float] = 0.0
    cgst_percentage: Optional[float] = 0.0

class OrderCreate(OrderBase):
    pass

class OrderStatusUpdate(BaseModel):
    status: str

class OrderDimensionsUpdate(BaseModel):
    height: float
    weight: float
    breadth: float
    length: float

class OrderResponse(OrderBase):
    id: int
    customer_name: Optional[str] = None  # Name from B2B or B2C application
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class DeliveryResponse(BaseModel):
    id: int
    order_id: int
    order_number: Optional[str] = None
    weight: float
    length: float
    breadth: float
    height: float
    awb_number: Optional[str] = None
    courier_partner: Optional[str] = None
    
    # GST Percentages
    sgst_percentage: Optional[float] = 0.0
    cgst_percentage: Optional[float] = 0.0
    igst_percentage: Optional[float] = 0.0
    gst_type: Optional[str] = None
    seller_gstin: Optional[str] = None
    
    pickup_location: str
    payment: str
    amount: float
    customer_name: str
    phone: str
    full_address: str
    email: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    item_name: Optional[str] = None
    quantity: int
    schedule_pickup: Optional[datetime] = None
    delivery_status: Optional[str] = None
    awb_label_path: Optional[str] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class DeliveryScheduleUpdate(BaseModel):
    schedule_pickup: datetime
