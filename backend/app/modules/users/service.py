from sqlalchemy.orm import Session
from sqlalchemy import cast as sa_cast, String, text
from typing import List, Optional, Union, Any
from app.modules.auth.models import EmployeeUser, User, AdminUser
from app.modules.auth.service import get_password_hash
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get all B2B/B2C users for display"""
    return db.query(User).filter(
        User.deleted_at.is_(None)
    ).offset(skip).limit(limit).all()

def get_all_employees(db: Session) -> List[Union[EmployeeUser, AdminUser]]:
    """Get all admin/staff users"""
    staff = db.query(EmployeeUser).filter(EmployeeUser.deleted_at.is_(None)).all()
    admins = db.query(AdminUser).filter(AdminUser.deleted_at.is_(None)).all()
    
    # Combine lists (admins first)
    return admins + staff

def get_employee_by_email(db: Session, email: str) -> Optional[Union[EmployeeUser, AdminUser]]:
    """Get an employee by email (checks both tables)"""
    # Check Admin first
    admin = db.query(AdminUser).filter(
        AdminUser.email == email,
        AdminUser.deleted_at.is_(None)
    ).first()
    if admin: return admin
    
    # Check Staff
    return db.query(EmployeeUser).filter(
        EmployeeUser.email == email,
        EmployeeUser.deleted_at.is_(None)
    ).first()

def create_employee(db: Session, employee_data: dict) -> Union[EmployeeUser, AdminUser]:
    """Create a new employee (admin/staff)"""
    hashed_password = get_password_hash(employee_data['password'])
    role = employee_data.get('role', 'staff').lower()
    
    if role == 'admin':
        new_admin = AdminUser(
            name=employee_data['name'],
            email=employee_data['email'],
            password=hashed_password,
            role='admin',
            status=employee_data.get('status', 'active').lower(),
            address=employee_data.get('address'),
            city=employee_data.get('city'),
            state=employee_data.get('state'),
            pincode=employee_data.get('pincode'),
            permissions=employee_data.get('permissions'),
            updated_at=datetime.utcnow()
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        return new_admin
    else:
        new_employee = EmployeeUser(
            name=employee_data['name'],
            email=employee_data['email'],
            password=hashed_password,
            role=role,
            status=employee_data.get('status', 'active').lower(),
            address=employee_data.get('address'),
            city=employee_data.get('city'),
            state=employee_data.get('state'),
            pincode=employee_data.get('pincode'),
            permissions=employee_data.get('permissions'),
            updated_at=datetime.utcnow()
        )
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)
        return new_employee

def reset_user_password(db: Session, user_id: Any, new_password: str) -> tuple[bool, str]:
    """Reset a user's password (admin action) across employee, admin, regular user, and auth_users"""
    from app.modules.orders.models import B2CApplication, B2BApplication
    from sqlalchemy import text
    import bcrypt

    str_id = str(user_id).strip()
    # Strip prefix if any (e.g. B2C-..., B2B-..., Admin-..., Staff-...)
    for prefix in ["B2C-", "B2B-", "Admin-", "Staff-", "b2c-", "b2b-", "admin-", "staff-"]:
        if str_id.startswith(prefix):
            str_id = str_id[len(prefix):].strip()
            break

    # 1. Try EmployeeUser
    if str_id.isdigit():
        int_id = int(str_id)
        employee = db.query(EmployeeUser).filter(
            EmployeeUser.id == int_id,
            EmployeeUser.deleted_at.is_(None)
        ).first()
        if employee:
            employee.password = get_password_hash(new_password)
            db.commit()
            return True, employee.email or "Employee"

        # 2. Try AdminUser
        admin = db.query(AdminUser).filter(
            AdminUser.id == int_id,
            AdminUser.deleted_at.is_(None)
        ).first()
        if admin:
            admin.password = get_password_hash(new_password)
            db.commit()
            return True, admin.email or "Admin"

        # 3. Try User
        user = db.query(User).filter(
            User.id == int_id,
            User.deleted_at.is_(None)
        ).first()
        if user:
            user.password = get_password_hash(new_password)
            db.commit()
            return True, user.email or "User"

    # 4. Try auth_users (B2C & B2B mobile customer users)
    bcrypt_hash = bcrypt.hashpw((new_password[:72]).encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 4a. Match auth_users directly by UUID / ID
    try:
        row = db.execute(text("SELECT id, email FROM auth_users WHERE id::text = :uid"), {"uid": str_id}).mappings().first()
        if row:
            db.execute(text("UPDATE auth_users SET password_hash = :ph WHERE id::text = :uid"), {"ph": bcrypt_hash, "uid": str_id})
            db.commit()
            return True, row['email'] or "Customer"
    except Exception as e:
        db.rollback()
        logger.warning(f"Error checking auth_users by ID: {e}")

    # 4b. Match via b2c_applications ID -> auth_users email
    try:
        b2c_row = db.execute(text("SELECT email FROM b2c_applications WHERE id::text = :uid"), {"uid": str_id}).mappings().first()
        if b2c_row and b2c_row['email']:
            row = db.execute(text("SELECT id, email FROM auth_users WHERE email = :email"), {"email": b2c_row['email']}).mappings().first()
            if row:
                db.execute(text("UPDATE auth_users SET password_hash = :ph WHERE email = :email"), {"ph": bcrypt_hash, "email": b2c_row['email']})
                db.commit()
                return True, b2c_row['email']
    except Exception as e:
        db.rollback()
        logger.warning(f"Error checking B2C application: {e}")

    # 4c. Match via b2b_applications ID -> auth_users email
    try:
        b2b_row = db.execute(text("SELECT email FROM b2b_applications WHERE id::text = :uid"), {"uid": str_id}).mappings().first()
        if b2b_row and b2b_row['email']:
            row = db.execute(text("SELECT id, email FROM auth_users WHERE email = :email"), {"email": b2b_row['email']}).mappings().first()
            if row:
                db.execute(text("UPDATE auth_users SET password_hash = :ph WHERE email = :email"), {"ph": bcrypt_hash, "email": b2b_row['email']})
                db.commit()
                return True, b2b_row['email']
    except Exception as e:
        db.rollback()
        logger.warning(f"Error checking B2B application: {e}")

    # 4d. Check if user_id is an email address
    if "@" in str_id:
        try:
            emp = db.query(EmployeeUser).filter(EmployeeUser.email == str_id).first()
            if emp:
                emp.password = get_password_hash(new_password)
                db.commit()
                return True, emp.email
            adm = db.query(AdminUser).filter(AdminUser.email == str_id).first()
            if adm:
                adm.password = get_password_hash(new_password)
                db.commit()
                return True, adm.email
            row = db.execute(text("SELECT id, email FROM auth_users WHERE email = :email"), {"email": str_id}).mappings().first()
            if row:
                db.execute(text("UPDATE auth_users SET password_hash = :ph WHERE email = :email"), {"ph": bcrypt_hash, "email": str_id})
                db.commit()
                return True, row['email']
        except Exception as e:
            db.rollback()
            logger.warning(f"Error checking by email: {e}")

    return False, "unknown"


from app.modules.orders.models import B2CApplication, B2BApplication

def update_user(db: Session, user_id: Any, user_type: str, update_data: dict) -> Optional[Any]:
    """Update a user/employee by ID and type"""
    logger.info(f"UPDATE_USER called: user_id={user_id}, user_type={user_type}, update_data={update_data}")
    target = None
    
    # Identify target table
    if user_type in ['Admin', 'Staff']:
        int_id = int(user_id) if str(user_id).isdigit() else user_id
        if user_type == 'Admin':
            logger.info(f"Looking for Admin with ID {int_id}")
            target = db.query(AdminUser).filter(AdminUser.id == int_id).first()
        else:
            logger.info(f"Looking for Staff (EmployeeUser) with ID {int_id}")
            target = db.query(EmployeeUser).filter(EmployeeUser.id == int_id).first()
    elif user_type == 'B2B':
        logger.info(f"Looking for B2B Application with ID {user_id}")
        target = db.query(B2BApplication).filter(sa_cast(B2BApplication.id, String) == str(user_id)).first()
        if not target:
            target = db.query(B2BApplication).filter(B2BApplication.id == str(user_id)).first()
        if target:
            # Map frontend 'name' to B2BApplication 'business_name'
            if 'name' in update_data:
                name_val = update_data.pop('name')
                if hasattr(target, 'business_name'):
                    target.business_name = name_val
                if hasattr(target, 'bussiness_name'):
                    target.bussiness_name = name_val
    elif user_type == 'B2C':
        logger.info(f"Looking for B2C Application with ID {user_id}")
        target = db.query(B2CApplication).filter(sa_cast(B2CApplication.id, String) == str(user_id)).first()
        if not target:
            try:
                target = db.query(B2CApplication).filter(B2CApplication.id == str(user_id)).first()
            except Exception:
                pass
        if target:
            # Map frontend 'name' to B2CApplication 'full_name'
            if 'name' in update_data and not hasattr(target, 'name'):
                update_data['full_name'] = update_data.pop('name')
    else:
        logger.info(f"Looking for User with ID {user_id}")
        if str(user_id).isdigit():
            target = db.query(User).filter(User.id == int(user_id)).first()
        else:
            target = db.query(User).filter(sa_cast(User.id, String) == str(user_id)).first()
        
    if not target:
        # Fallback to User table if not found
        try:
            if str(user_id).isdigit():
                target = db.query(User).filter(User.id == int(user_id)).first()
            else:
                target = db.query(User).filter(sa_cast(User.id, String) == str(user_id)).first()
        except Exception:
            pass

    if not target:
        logger.error(f"Target user not found: user_id={user_id}, user_type={user_type}")
        return None
    
    logger.info(f"Found target: {target.__class__.__name__}")
        
    # Update fields
    for key, value in update_data.items():
        if hasattr(target, key) and value is not None:
            # Convert role and status to lowercase to match DB constraints
            if key in ['role', 'status'] and isinstance(value, str):
                value = value.lower()
            logger.info(f"Setting {key} = {value}")
            setattr(target, key, value)
    
    try:
        db.commit()
        db.refresh(target)
        logger.info(f"Successfully updated user {user_id}")
        return target
    except Exception as e:
        logger.error(f"Error committing update: {e}")
        db.rollback()
        raise

def get_all_b2c_users(db: Session):
    return db.query(B2CApplication).all()

def get_all_b2b_users(db: Session):
    return db.query(B2BApplication).all()

def delete_user_by_type(db: Session, user_id: Any, user_type: str) -> bool:
    """Delete a user/employee by ID and type"""
    target = None
    
    if user_type in ['Admin', 'Staff']:
        int_id = int(user_id) if str(user_id).isdigit() else user_id
        if user_type == 'Admin':
            target = db.query(AdminUser).filter(AdminUser.id == int_id).first()
        else:
            target = db.query(EmployeeUser).filter(EmployeeUser.id == int_id).first()
    elif user_type == 'B2B':
        target = db.query(B2BApplication).filter(sa_cast(B2BApplication.id, String) == str(user_id)).first()
        if not target:
            target = db.query(B2BApplication).filter(B2BApplication.id == str(user_id)).first()
    elif user_type == 'B2C':
        target = db.query(B2CApplication).filter(sa_cast(B2CApplication.id, String) == str(user_id)).first()
        if not target:
            target = db.query(B2CApplication).filter(B2CApplication.id == str(user_id)).first()
    else:
        if str(user_id).isdigit():
            target = db.query(User).filter(User.id == int(user_id)).first()
        else:
            target = db.query(User).filter(sa_cast(User.id, String) == str(user_id)).first()
        
    if target:
        db.delete(target)
        db.commit()
        return True
        
    return False
