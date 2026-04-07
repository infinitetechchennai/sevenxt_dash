from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum
from sqlalchemy.sql import func
from app.database import Base

class EmployeeUser(Base):
    __tablename__ = "employee_users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default="staff", index=True)
    status = Column(String(50), default="active", index=True)
    
    # Address fields
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    
    
    # Permissions for staff users (stored as JSON)
    permissions = Column(JSON, nullable=True)
    
    # Password Reset Fields
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # Metadata
    phone = Column(String(15), nullable=True)
    profile_picture = Column(String(500), nullable=True)  # Profile picture URL/path
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    status = Column(String(50), default="active")
    
    # Address fields
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    
    # Permissions
    permissions = Column(JSON, nullable=True)
    
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)


class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default="admin", index=True)
    status = Column(String(50), default="active", index=True)
    
    # Address fields
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    
    # Permissions
    permissions = Column(JSON, nullable=True)
    
    # Password Reset Fields
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # Metadata
    phone = Column(String(15), nullable=True)
    profile_picture = Column(String(500), nullable=True)  # Profile picture URL/path
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
