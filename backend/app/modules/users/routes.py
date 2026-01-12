from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.modules.users import schemas, service
from app.modules.auth.models import EmployeeUser, User, AdminUser
from typing import Any, Union
from app.modules.auth.routes import get_current_employee
from app.modules.activity_logs.service import log_activity
import logging

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users Management"])

employees_router = APIRouter(prefix="/employees", tags=["Employees Management"])


@router.get("/b2c", response_model=list[schemas.B2CUserResponse])
def read_b2c_users(db: Session = Depends(get_db)):
    """Get all B2C users"""
    return service.get_all_b2c_users(db)

from fastapi.responses import JSONResponse

@router.get("/b2b", response_model=list[schemas.B2BUserResponse])
def read_b2b_users(db: Session = Depends(get_db)):
    """Get all B2B users"""
    try:
        return service.get_all_b2b_users(db)
    except Exception as e:
        print(f"Error fetching B2B users: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("", response_model=list[schemas.UserResponse])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Get all regular users (Display only)"""
    users = service.get_all_users(db, skip=skip, limit=limit)
    return users

@router.delete("/{user_id}")
def delete_user(
    user_id: int, 
    type: str = None,
    db: Session = Depends(get_db),
    current_user: Union[EmployeeUser, AdminUser] = Depends(get_current_employee)
):
    """Delete a user (soft delete)"""
    if type:
        success = service.delete_user_by_type(db, user_id, type)
        if success:
            # Log activity
            log_activity(
                db=db,
                action="Deleted User",
                module="Users",
                user_id=str(current_user.id),
                user_name=current_user.name,
                user_type=current_user.role.capitalize(),
                details=f"Deleted {type} user with ID: {user_id}",
                status="Success",
                affected_entity_type="User",
                affected_entity_id=str(user_id)
            )
            return {"message": f"{type} user deleted successfully"}
        raise HTTPException(status_code=404, detail="User not found")

    # Fallback to old logic if type not provided
    # Try to find in employee_users table first (Admin/Staff)
    employee = db.query(EmployeeUser).filter(
        EmployeeUser.id == user_id,
        EmployeeUser.deleted_at.is_(None)
    ).first()
    
    if employee:
        employee.deleted_at = datetime.utcnow()
        db.commit()
        
        # Log activity
        log_activity(
            db=db,
            action="Deleted Employee",
            module="Users",
            user_id=str(current_user.id),
            user_name=current_user.name,
            user_type=current_user.role.capitalize(),
            details=f"Deleted employee: {employee.name} ({employee.email})",
            status="Success",
            affected_entity_type="Employee",
            affected_entity_id=str(user_id)
        )
        
        return {"message": "Employee deleted successfully", "type": "employee"}
    
    # Try to find in users table (B2B/B2C)
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()
    
    if user:
        user.deleted_at = datetime.utcnow()
        db.commit()
        
        # Log activity
        log_activity(
            db=db,
            action="Deleted User",
            module="Users",
            user_id=str(current_user.id),
            user_name=current_user.name,
            user_type=current_user.role.capitalize(),
            details=f"Deleted user: {user.email}",
            status="Success",
            affected_entity_type="User",
            affected_entity_id=str(user_id)
        )
        
        return {"message": "User deleted successfully", "type": "user"}
    
    raise HTTPException(status_code=404, detail="User not found")

@router.put("/{user_id}")
def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
<<<<<<< HEAD
    user_type: str = Query(..., alias="type"), # Use alias to match frontend query param 'type'
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_employee)
):
    """Update a user/employee"""
    try:
        updated_user = service.update_user(db, user_id, user_type, user_data.dict(exclude_unset=True))
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Determine current user's name and type
        current_user_name = current_user.name if hasattr(current_user, 'name') else 'Unknown'
        
        # Check if user is Admin by model type
        from app.modules.auth.models import AdminUser, EmployeeUser
        
        # Debug logging
        logger.info(f"DEBUG: current_user type = {type(current_user)}")
        logger.info(f"DEBUG: current_user.__class__.__name__ = {current_user.__class__.__name__}")
        logger.info(f"DEBUG: isinstance(current_user, AdminUser) = {isinstance(current_user, AdminUser)}")
        logger.info(f"DEBUG: isinstance(current_user, EmployeeUser) = {isinstance(current_user, EmployeeUser)}")
        logger.info(f"DEBUG: current_user.role = {current_user.role if hasattr(current_user, 'role') else 'NO ROLE ATTR'}")
        
        # Determine user type based on MODEL CLASS (not role field)
        # AdminUser table = Admin, EmployeeUser table = Staff
        if isinstance(current_user, AdminUser):
            current_user_type = 'Admin'
            logger.info("DEBUG: User type set to Admin (from AdminUser table)")
        elif isinstance(current_user, EmployeeUser):
            current_user_type = 'Staff'
            logger.info("DEBUG: User type set to Staff (from EmployeeUser table)")
        else:
            # Fallback to role check if model type is unclear
            if hasattr(current_user, 'role') and current_user.role == 'admin':
                current_user_type = 'Admin'
                logger.info("DEBUG: User type set to Admin (by role fallback)")
            else:
                current_user_type = 'Staff'
                logger.info("DEBUG: User type set to Staff (by default fallback)")
        
        
        # Log activity
        log_activity(
            db=db,
            action="Updated User",
            module="Users",
            user_name=current_user_name,
            user_type=current_user_type,
            details=f"Updated {user_type} user with ID: {user_id} (Name: {updated_user.name if hasattr(updated_user, 'name') else 'N/A'})",
            status="Success",
            affected_entity_type="User",
            affected_entity_id=str(user_id)
        )
        
        return {"message": "User updated successfully", "user": updated_user}
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))
=======
    type: str,
    db: Session = Depends(get_db),
    current_user: Union[EmployeeUser, AdminUser] = Depends(get_current_employee)
):
    """Update a user/employee"""
    updated_user = service.update_user(db, user_id, type, user_data.dict(exclude_unset=True))
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log activity
    log_activity(
        db=db,
        action="Updated User",
        module="Users",
        user_id=str(current_user.id),
        user_name=current_user.name,
        user_type=current_user.role.capitalize(),
        details=f"Updated {type} user with ID: {user_id}",
        status="Success",
        affected_entity_type="User",
        affected_entity_id=str(user_id)
    )
    
    return {"message": "User updated successfully", "user": updated_user}
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7

# ========== EMPLOYEES ROUTER ==========

@employees_router.get("", response_model=list[schemas.EmployeeResponse])
def get_employees(
    db: Session = Depends(get_db)
):
    """Get all employees (Admin/Staff)"""
    employees = service.get_all_employees(db)
    return employees

@employees_router.post("/create", response_model=schemas.EmployeeResponse)
def create_employee(
    employee_data: schemas.EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: Union[EmployeeUser, AdminUser] = Depends(get_current_employee)
):
    """Create a new employee (admin/staff)"""
    try:
        print(f"DEBUG: create_employee HIT with data: {employee_data.dict()}")
        # Check if email already exists
        existing = service.get_employee_by_email(db, employee_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create employee
        new_employee = service.create_employee(db, employee_data.dict())
        
        # Log activity
        log_activity(
            db=db,
            action="Created Employee",
            module="Users",
            user_id=str(current_user.id),
            user_name=current_user.name,
            user_type=current_user.role.capitalize(),
            details=f"Created new {employee_data.role} employee: {employee_data.name} ({employee_data.email})",
            status="Success",
            affected_entity_type="Employee",
            affected_entity_id=str(new_employee.id) if new_employee else None
        )
        
        return new_employee
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR creating employee: {e}")
        
        # Log failed activity
        log_activity(
            db=db,
            action="Failed to Create Employee",
            module="Users",
            user_id=str(current_user.id),
            user_name=current_user.name,
            user_type=current_user.role.capitalize(),
            details=f"Failed to create employee: {employee_data.email}. Error: {str(e)}",
            status="Failed"
        )
        
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# ========== ADMIN PASSWORD RESET ==========

@router.post("/admin/reset-password", response_model=schemas.ResetPasswordResponse)
def admin_reset_password(
    request: schemas.ResetPasswordAdminRequest,
    db: Session = Depends(get_db),
    current_employee: Any = Depends(get_current_employee)
):
    """Admin endpoint to reset a user's password directly"""
    
    # Only admins can reset passwords
    if current_employee.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can reset user passwords"
        )
    
    # Reset password
    success = service.reset_user_password(db, request.user_id, request.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or failed to reset"
        )
    
    # Fetch user email for response
    email = "unknown"
    emp = db.query(EmployeeUser).filter(EmployeeUser.id == request.user_id).first()
    if emp: email = emp.email
    else:
        usr = db.query(User).filter(User.id == request.user_id).first()
        if usr: email = usr.email

    return {
        "message": "Password reset successfully",
        "user_id": request.user_id,
        "email": email,
        "password_updated": True
    }
