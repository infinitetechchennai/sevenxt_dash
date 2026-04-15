from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ActivityLogCreate(BaseModel):
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_type: Optional[str] = None
    action: str
    module: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    status: str = "Success"
    affected_entity_type: Optional[str] = None
    affected_entity_id: Optional[str] = None


class ActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[str]
    user_name: Optional[str]
    user_type: Optional[str]
    action: str
    module: str
    details: Optional[str]
    ip_address: Optional[str]
    status: str
    affected_entity_type: Optional[str]
    affected_entity_id: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True
