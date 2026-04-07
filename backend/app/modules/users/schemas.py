from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum
from uuid import UUID

class B2BStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class B2CUserResponse(BaseModel):
    id: UUID
    full_name: Optional[str]
    email: Optional[str]
    phone_number: Optional[Union[str, int]]
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class B2BUserResponse(BaseModel):
    id: UUID
    business_name: Optional[str]
    gstin: Optional[str]
    pan: Optional[str]
    email: Optional[str]
    phone_number: Optional[Union[str, int]]
    status: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

# Keep existing schemas
class UserBase(BaseModel):
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    permissions: Optional[List[str]] = None

class UserResponse(UserBase):
    id: int
    name: Optional[str] = None
    role: Optional[str] = "user"
    status: Optional[str] = "active"
    created_at: datetime
    permissions: Optional[List[str]] = []

    class Config:
        from_attributes = True

class EmployeeCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str
    status: str = "Active"
    permissions: Optional[List[str]] = []
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

class EmployeeResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    status: str
    permissions: Optional[List[str]] = []
    created_at: datetime
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    class Config:
        from_attributes = True

class ResetPasswordResponse(BaseModel):
    message: str
    status: str

class ResetPasswordAdminRequest(BaseModel):
    user_id: int
    new_password: str
