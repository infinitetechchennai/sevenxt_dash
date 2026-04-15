from sqlalchemy import Column, Integer, String, Date, Float
from app.database import Base

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    
    # Mapping 'type' to 'discount_type' in DB
    type = Column("discount_type", String(20), nullable=False)
    
    # Mapping 'value' to 'discount_value' in DB
    value = Column("discount_value", String(20), nullable=False)
    
    target = Column(String(10), nullable=False)
    usage_count = Column(String(20), default="0/100") # Updated default to match your image (100)
    status = Column(String(20), default="Active")
    expiry = Column(Date, nullable=True)
    
    # --- NEW WORKFLOW FIELDS ---
    min_order_value = Column(String(20), nullable=True, default="0")
    
    # Note: Your image doesn't show a separate 'usage_limit' column, 
    # but it appears to be part of the 'usage_count' string (e.g., "0/100").
    usage_limit = Column(String(20), nullable=True, default="100") 
    
    razorpay_offer_id = Column(String(100), nullable=True)
class FlashDeal(Base):
    __tablename__ = "flash_deals"
    id = Column(Integer, primary_key=True)
    product = Column(String(200))
    original_price = Column(Float)
    deal_price = Column(Float)
    discount = Column(String(10))
    ends_in = Column(String(50))
    status = Column(String(20))
    target = Column(String(10))

# ... Banner and AdCampaign models remain unchanged ...