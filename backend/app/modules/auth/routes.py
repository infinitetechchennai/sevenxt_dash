from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime
from app.database import get_db
from app.config import settings
from app.modules.auth import schemas, service
from app.modules.auth.models import EmployeeUser, User, AdminUser
from typing import Union, Any

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login-json")

def get_current_employee(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Union[EmployeeUser, AdminUser]:
    """Get the current authenticated employee"""
    print(f"DEBUG: get_current_employee called with token: {token[:10]}...")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    employee = service.get_employee_by_email(db, email=email)
    if employee is None:
        raise credentials_exception
    
    return employee

@router.post("/login-json", response_model=schemas.Token)
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint for admin/staff"""
    print(f"DEBUG LOGIN: Received email='{login_data.email}', password='{login_data.password}'")
    employee = service.authenticate_employee(db, login_data.email, login_data.password)
    print(f"DEBUG LOGIN: Result={employee}")
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = service.create_access_token(
        data={"sub": employee.email, "role": employee.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": employee
    }

@router.post("/register", response_model=schemas.UserResponse)
def register(
    user_data: schemas.EmployeeCreate,
    db: Session = Depends(get_db)
):
    """Register a new B2B/B2C user"""
    # Check if email already exists
    existing = service.get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    new_user = service.create_user(db, user_data.dict())
    return new_user

@router.get("/me", response_model=schemas.EmployeeResponse)
def read_users_me(current_employee: Any = Depends(get_current_employee)):
    """Get current logged in employee details"""
    return current_employee




# ========== USER-FACING PASSWORD RESET (OTP) ==========

# Handle preflight for forgot password explicitly if global Middleware fails
@router.options("/forgot-password")
async def forgot_password_options():
    return {}

@router.post("/forgot-password", response_model=schemas.ForgotPasswordResponse)
def forgot_password(
    request: schemas.ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Request password reset - sends OTP to email via SendGrid"""
    try:
        print(f"Forgot password request for: {request.email}")
        
        result = service.request_password_reset_otp(db, request.email)

        if not result:
            # Don't reveal if email exists for security
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        return {
            "message": "OTP sent to your email"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"CRITICAL ERROR in forgot_password: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(e)}"
        )


@router.post("/reset-password-otp", response_model=schemas.MessageResponse)
def reset_password_otp(
    request: schemas.ResetPasswordOTPRequest,
    db: Session = Depends(get_db)
):
    """Reset password using OTP"""
    success = service.reset_password_with_otp(db, request.email, request.otp, request.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP or expired"
        )
    
    return {"message": "Password has been reset successfully"}

# ========== PROFILE PICTURE UPLOAD ==========

from fastapi import File, UploadFile

@router.post("/upload-profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_employee: Any = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Upload profile picture for current user"""
    try:
        from app.utils.cloudinary_upload import upload_image_to_cloudinary
        contents = await file.read()
        profile_picture_url = upload_image_to_cloudinary(
            file_bytes=contents,
            folder="sevenxt/profiles",
            resize_width=300,
            quality=85,
        )

        # Update database based on user type
        if isinstance(current_employee, AdminUser):
            current_employee.profile_picture = profile_picture_url
        elif isinstance(current_employee, EmployeeUser):
            current_employee.profile_picture = profile_picture_url

        db.commit()
        db.refresh(current_employee)

        return {
            "message": "Profile picture uploaded successfully",
            "profile_picture": profile_picture_url
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )

@router.get("/profile")
def get_profile(
    current_employee: Any = Depends(get_current_employee)
):
    """Get current user profile with picture"""
    return {
        "id": current_employee.id,
        "name": current_employee.name,
        "email": current_employee.email,
        "phone": current_employee.phone,
        "role": current_employee.role,
        "profile_picture": current_employee.profile_picture,
        "address": current_employee.address if hasattr(current_employee, "address") else None,
        "city": current_employee.city if hasattr(current_employee, "city") else None,
        "state": current_employee.state if hasattr(current_employee, "state") else None,
        "pincode": current_employee.pincode if hasattr(current_employee, "pincode") else None,
        "permissions": current_employee.permissions if hasattr(current_employee, "permissions") else [],
        "user_type": "admin" if isinstance(current_employee, AdminUser) else "employee"
    }

@router.put("/profile")
def update_profile(
    profile_data: dict,
    current_employee: Any = Depends(get_current_employee),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    try:
        if "name" in profile_data:
            current_employee.name = profile_data["name"]
        if "phone" in profile_data:
            current_employee.phone = profile_data["phone"]
        if "email" in profile_data:
            current_employee.email = profile_data["email"]
        if "address" in profile_data:
            current_employee.address = profile_data["address"]
        if "city" in profile_data:
            current_employee.city = profile_data["city"]
        if "state" in profile_data:
            current_employee.state = profile_data["state"]
        if "pincode" in profile_data:
            current_employee.pincode = profile_data["pincode"]
        
        db.commit()
        db.refresh(current_employee)
        
        return {
            "message": "Profile updated successfully",
            "profile": {
                "id": current_employee.id,
                "name": current_employee.name,
                "email": current_employee.email,
                "phone": current_employee.phone,
                "role": current_employee.role,
                "profile_picture": current_employee.profile_picture,
                "address": current_employee.address,
                "city": current_employee.city,
                "state": current_employee.state,
                "pincode": current_employee.pincode
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )
# Trigger reload
