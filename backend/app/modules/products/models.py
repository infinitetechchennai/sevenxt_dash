from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(String(50), primary_key=True, index=True) # Using String ID to match frontend "prod_" generation or UUID
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    colors = Column(String(255), nullable=True)  # Store product colors
    brand_name = Column(String(100), nullable=True)  # Store product brand name
    
    # Pricing
    b2c_price = Column(Float, default=0.0)
    compare_at_price = Column(Float, default=0.0) # MRP
    b2b_price = Column(Float, default=0.0)
    
    # Offers
    b2c_active_offer = Column(Float, default=0.0) # Renamed from b2c_offer_percentage
    b2c_discount = Column(Float, default=0.0) # Discount for B2C
    b2c_offer_price = Column(Float, default=0.0) # Calculated Offer Price
    b2c_offer_start_date = Column(DateTime, nullable=True)
    b2c_offer_end_date = Column(DateTime, nullable=True)
    
    b2b_active_offer = Column(Float, default=0.0) # Renamed from b2b_offer_percentage
    b2b_discount = Column(Float, default=0.0) # Bulk discount for B2B
    b2b_offer_price = Column(Float, default=0.0) # Calculated Offer Price
    b2b_offer_start_date = Column(DateTime, nullable=True)
    b2b_offer_end_date = Column(DateTime, nullable=True)
    
    info = Column(Text(length=4294967295), nullable=True)
    description = Column(Text(length=4294967295), nullable=True)  # Detailed product description
    status = Column(String(50), default="Draft") # Active, Draft, Archived
    stock = Column(Integer, default=0)
    image = Column(Text(length=4294967295), nullable=True) # LONGTEXT
    
    rating = Column(Float, default=0.0)
    # reviews = Column(Integer, default=0)
    
    # Tax and Compliance
    sgst = Column(Float, default=0.0)  # SGST percentage (State GST)
    cgst = Column(Float, default=0.0)  # CGST percentage (Central GST)
    hsn = Column(String(20), nullable=True)  # HSN code
    # return_policy = Column(Text, nullable=True)  # Return policy description
    
    # Dimensions (for shipping)
    height = Column(Float, default=0.0)  # in cm
    weight = Column(Float, default=0.0)  # in kg
    breadth = Column(Float, default=0.0)  # in cm
    length = Column(Float, default=0.0)  # in cm
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    attributes = relationship("ProductAttribute", back_populates="product", cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

class ProductAttribute(Base):
    __tablename__ = "product_attributes"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(50), ForeignKey("products.id"))
    name = Column(String(100))
    value = Column(String(255))
    
    product = relationship("Product", back_populates="attributes")

class ProductVariant(Base):
    __tablename__ = "product_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(50), ForeignKey("products.id"))
    color = Column(String(50))
    color_code = Column(String(20))
    stock = Column(Integer, default=0)
    
    product = relationship("Product", back_populates="variants")
