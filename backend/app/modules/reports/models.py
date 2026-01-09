from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# We reference existing tables from your SQL dump
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    order_id = Column(String, unique=True)
    customer_type = Column(String) # B2B or B2C
    products = Column(JSON) # JSONB field containing product array
    amount = Column(Float)
    created_at = Column(DateTime, default=func.now())

class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(Integer, primary_key=True)
    delivery_status = Column(String) # e.g., DELIVERED, Pickup