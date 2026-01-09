from datetime import datetime, timedelta
from typing import Optional, List, Union
from jose import JWTError, jwt
# from passlib.context import CryptContext  # Causing crashes on Windows
from sqlalchemy.orm import Session
from app.config import settings
from app.modules.auth.models import EmployeeUser, User, AdminUser

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

import hashlib
import os
import random

def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP"""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

def get_password_hash(password: str) -> str:
    """Hash a password using SHA-256 with a salt"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ':' + key.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        # Check for bcrypt hash (starts with $2b$ or $2a$ or $2y$)
        if hashed_password.startswith('$2'):
            import bcrypt
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        
        # Check for PBKDF2 hash (contains ':')
        if ':' in hashed_password:
            salt_hex, key_hex = hashed_password.split(':')
            salt = bytes.fromhex(salt_hex)
            key = bytes.fromhex(key_hex)
            new_key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
            return new_key == key
        
        # Check for plain text (legacy/temporary)
        return plain_password == hashed_password
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def authenticate_employee(db: Session, email: str, password: str) -> Optional[Union[EmployeeUser, AdminUser]]:
    """Authenticate an employee (admin/staff) by email and password"""
    
    # Check AdminUser first
    admin = db.query(AdminUser).filter(
        AdminUser.email == email,
        AdminUser.deleted_at.is_(None)
    ).first()
    
    if admin:
        if admin.status and admin.status.lower() != "active": return None
        if verify_password(password, admin.password):
            # Update last login
            try:
                admin.last_login = datetime.utcnow()
                db.commit()
                db.refresh(admin)
            except Exception:
                db.rollback()
            return admin
            
    # Check EmployeeUser
    employee = db.query(EmployeeUser).filter(
        EmployeeUser.email == email,
        EmployeeUser.deleted_at.is_(None)
    ).first()
    
    if employee:
        if employee.status and employee.status.lower() != "active": return None
        if verify_password(password, employee.password):
            # Update last login
            try:
                employee.last_login = datetime.utcnow()
                db.commit()
                db.refresh(employee)
            except Exception:
                db.rollback()
            return employee
            
    return None

def get_employee_by_email(db: Session, email: str) -> Optional[Union[EmployeeUser, AdminUser]]:
    """Get an employee by email"""
    # Check AdminUser first
    try:
        admin = db.query(AdminUser).filter(
            AdminUser.email == email,
            AdminUser.deleted_at.is_(None)
        ).first()
        if admin: return admin
    except Exception:
        db.rollback()

    try:
        return db.query(EmployeeUser).filter(
            EmployeeUser.email == email,
            EmployeeUser.deleted_at.is_(None)
        ).first()
    except Exception:
        db.rollback()
        
    return None



def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a B2B/B2C user by email"""
    return db.query(User).filter(
        User.email == email,
        User.deleted_at.is_(None)
    ).first()

def create_user(db: Session, user_data: dict) -> User:
    """Create a new B2B/B2C user"""
    # Hash the password
    hashed_password = get_password_hash(user_data['password'])
    
    # Create user object
    new_user = User(
        name=user_data['name'],
        email=user_data['email'],
        password=hashed_password,
        role=user_data.get('role', 'user'),
        status=user_data.get('status', 'active'),
        address=user_data.get('address'),
        city=user_data.get('city'),
        state=user_data.get('state'),
        pincode=user_data.get('pincode'),
        permissions=user_data.get('permissions')
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

# ========== OTP PASSWORD RESET (SENDGRID) ==========

from app.modules.auth.sendgrid_utils import sendgrid_service

def request_password_reset_otp(db: Session, email: str) -> Optional[str]:
    """Generate OTP, store it in DB, and send via SendGrid"""
    
    # Check Admin
    admin = db.query(AdminUser).filter(AdminUser.email == email, AdminUser.deleted_at.is_(None)).first()
    
    # Check Employee
    employee = db.query(EmployeeUser).filter(EmployeeUser.email == email, EmployeeUser.deleted_at.is_(None)).first()
    
    # Check User
    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
    
    target = admin or employee or user
    if not target: return None
    
    # Generate OTP
    otp = generate_otp()
    otp_expires = datetime.utcnow() + timedelta(minutes=10)
    
    target.reset_token = otp
    target.reset_token_expires = otp_expires
    
    db.commit()
    
    # Send OTP via SendGrid
    sent = sendgrid_service.send_otp_email(email, otp)
    print(f"🔐 OTP for {email}: {otp}")
    
    if not sent:
        return "sent_fallback"
        
    return "sent_via_sendgrid"

def reset_password_with_otp(db: Session, email: str, otp: str, new_password: str) -> bool:
    """Verify OTP from database and reset password"""
    
    admin = db.query(AdminUser).filter(AdminUser.email == email, AdminUser.deleted_at.is_(None)).first()
    employee = db.query(EmployeeUser).filter(EmployeeUser.email == email, EmployeeUser.deleted_at.is_(None)).first()
    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
    
    target = admin or employee or user
    if not target: return False
    
    if not target.reset_token or target.reset_token != otp:
        return False
    if target.reset_token_expires and target.reset_token_expires < datetime.utcnow():
        return False
        
    target.password = get_password_hash(new_password)
    target.reset_token = None
    target.reset_token_expires = None
    
    db.commit()
    return True

