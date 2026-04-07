from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SettingBase(BaseModel):
    category: str
    key: str
    value: Optional[str] = None
    data_type: str = 'string'
    description: Optional[str] = None

class SettingCreate(SettingBase):
    pass

class SettingUpdate(BaseModel):
    value: str

class SettingResponse(SettingBase):
    id: int
    is_active: bool
    updated_at: datetime
    updated_by: Optional[int] = None
    
    class Config:
        from_attributes = True

# Stock Alert specific schemas
class StockAlertSettings(BaseModel):
    low_stock_threshold: int = 10
    enable_email_alerts: bool = True
    enable_dashboard_alerts: bool = True
    alert_email: Optional[str] = None
    
class StockAlertUpdate(BaseModel):
    low_stock_threshold: Optional[int] = None
    enable_email_alerts: Optional[bool] = None
    enable_dashboard_alerts: Optional[bool] = None
    alert_email: Optional[str] = None
