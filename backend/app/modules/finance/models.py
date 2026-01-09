from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Razorpay IDs
    razorpay_order_id = Column(String(100), unique=True, index=True, nullable=True)
    razorpay_payment_id = Column(String(100), unique=True, index=True, nullable=True)
    razorpay_signature = Column(String(255), nullable=True)
    
    # Internal Tracking
    internal_order_id = Column(String(100), nullable=True) 
    user_email = Column(String(255), nullable=False)
    customer_contact = Column(String(20), nullable=True)
    
    # Financials
    amount = Column(Numeric(10, 2), nullable=False)
    
    # --- NEW TAX COLUMNS (DO NOT DELETE) ---
    fee = Column(Numeric(10, 2), default=0.0) # Razorpay Platform Fee
    tax = Column(Numeric(10, 2), default=0.0) # GST on Fee (Tax data)
    
    currency = Column(String(10), default="INR")
    method = Column(String(50), nullable=True) # card, upi, etc.
    gateway = Column(String(50), default="Razorpay")
    
    # Status
    status = Column(String(50), default="PENDING") # SUCCESS, FAILED, PENDING, REFUNDED
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())