from sqlalchemy import Column, Integer, String, DECIMAL, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class B2BApplication(Base):
    __tablename__ = "b2b_applications"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    business_name = Column(Text, nullable=False)
    gstin = Column(String(20), nullable=False)
    pan = Column(String(15), nullable=False)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    gst_certificate_url = Column(Text, nullable=True)
    business_license_url = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default='pending_approval')
    state = Column(String(100), nullable=True)
    registration_date = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    address_id = Column(UUID(as_uuid=True), nullable=True)

class B2CApplication(Base):
    __tablename__ = "b2c_applications"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(Text, nullable=True)
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    email = Column(String(255), nullable=True)
    address_id = Column(UUID(as_uuid=True), nullable=True)

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, index=True)
    customer_type = Column(String(50))

    # Direct customer name (No Foreign Keys)
    customer_name = Column(String(255), nullable=True)

    products = Column(JSON)
    amount = Column(DECIMAL(10, 2))
    payment = Column(String(50))
    status = Column(String(50))
    awb_number = Column(String(50), nullable=True)
    address = Column(Text)
    email = Column(String(100))
    phone = Column(String(20))
    
    # Location fields
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    
    # Dimensions
    height = Column(Integer, nullable=True)
    weight = Column(Integer, nullable=True)
    breadth = Column(Integer, nullable=True)
    length = Column(Integer, nullable=True)
    
    # HSN Code
    hsn = Column(String(20), nullable=True)

    # GST Percentages
    sgst_percentage = Column(DECIMAL(5, 2), nullable=True, default=0.00)
    cgst_percentage = Column(DECIMAL(5, 2), nullable=True, default=0.00)
    razorpay_order_id = Column(String(50), nullable=True)

    # GST and Pricing fields
    original_price = Column(DECIMAL(10, 2), nullable=True)  # Price before tax
    sgst_percentage = Column(DECIMAL(5, 2), nullable=True)  # SGST percentage (e.g., 9.00 for 9%)
    cgst_percentage = Column(DECIMAL(5, 2), nullable=True)  # CGST percentage (e.g., 9.00 for 9%)
    hsn = Column(String(20), nullable=True)  # HSN code

    #return AWb number annd label
    # return_awb_number = Column(String(255), nullable=True)
    # return_label_path = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exchanges = relationship("Exchange", back_populates="order")

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    order = relationship("Order")
    
    weight = Column(DECIMAL(6, 2), nullable=False)
    length = Column(DECIMAL(6, 2), nullable=False)
    breadth = Column(DECIMAL(6, 2), nullable=False)
    height = Column(DECIMAL(6, 2), nullable=False)
    
    awb_number = Column(String(255), nullable=True)
    courier_partner = Column(String(50), default='Delhivery')
    pickup_location = Column(String(100), nullable=False)
    payment = Column(String(11), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    customer_name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=False)
    full_address = Column(Text, nullable=False)
    
    # Location fields
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    
    item_name = Column(String(255), nullable=True)
    quantity = Column(Integer, nullable=False)
    schedule_pickup = Column(DateTime, nullable=True)
    delivery_status = Column(String(50), default='Ready to Pickup')
    awb_label_path = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
