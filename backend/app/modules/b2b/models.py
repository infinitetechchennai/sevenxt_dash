from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class B2BApplication(Base):
    __tablename__ = "b2b_applications"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    
    # We map 'bussiness_name' (used in code/frontend) 
    # to 'business_name' (the real column in your database)
    bussiness_name = Column("business_name", String(255), nullable=False)
    
    gstin = Column(String(15), nullable=False)
    pan = Column(String(10), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    
    # Treat as string in Python to avoid the 2147483647 integer crash
    phone_number = Column(String(20), nullable=False)
    
    gst_certificate_url = Column(String(500), nullable=True)
    business_license_url = Column(String(500), nullable=True)
    status = Column(String(50), default="Pending")
    state = Column(String(100), nullable=True)
    registration_date = Column(String(50), nullable=True)
    address_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())