from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# Login Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "staff"
    status: str = "active"
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    permissions: Optional[Any] = None

# User Response Schemas
class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    permissions: Optional[Any] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Employee Response Schema
class EmployeeResponse(UserResponse):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str
    user: EmployeeResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    user_type: Optional[str] = None

# Admin Password Reset Schemas
class ResetPasswordAdminRequest(BaseModel):
    user_id: int
    new_password: str

class ResetPasswordResponse(BaseModel):
    message: str
    user_id: int
    email: str
    password_updated: bool

# User-Facing Password Reset Schemas (OTP)
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordResponse(BaseModel):
    message: str
    dev_otp: Optional[str] = None  # For development only

class ResetPasswordOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

class MessageResponse(BaseModel):
    message: str




