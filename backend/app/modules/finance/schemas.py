from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    internal_order_id: str
    user_email: str
    amount: float

class TransactionResponse(BaseModel):
    id: int
    razorpay_order_id: str
    razorpay_payment_id: Optional[str]
    internal_order_id: str
    amount: float
    status: str
    method: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)