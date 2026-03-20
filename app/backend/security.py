from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

import os

# --- Configuration ---
# IMPORTANT: In a real application, you should load this from a secure config file, not hardcode it.
# Use a long, random string for your actual secret key.
SECRET_KEY = os.getenv("SECRET_KEY", "a-very-secret-key-that-you-should-change")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))  # The token will be valid for 30 minutes

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- JWT Token Creation ---
# In security.py - update create_access_token function

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, user_id: Optional[str] = None, user_type: Optional[str] = None):
    """Creates a new JWT access token."""
    to_encode = data.copy()
    
    # Set the token expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Add user_id and user_type if provided
    if user_id:
        to_encode.update({"user_id": user_id})
    if user_type:
        to_encode.update({"user_type": user_type})
    
    # Encode the token with your secret key and algorithm
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt