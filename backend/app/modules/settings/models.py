from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Setting(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)  # 'inventory', 'delivery', 'business', etc.
    key = Column(String(100), nullable=False)  # 'low_stock_threshold', 'enable_alerts', etc.
    value = Column(Text, nullable=True)  # The actual value
    data_type = Column(String(20), default='string')  # 'string', 'number', 'boolean', 'json'
    description = Column(Text, nullable=True)  # Human-readable description
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, nullable=True)  # Employee ID who updated
    
    class Config:
        orm_mode = True
