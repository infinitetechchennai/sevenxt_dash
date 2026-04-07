"""
Helper function to get current user name for activity logging
"""
from typing import Optional
from app.modules.auth.models import EmployeeUser, AdminUser

def get_user_name_for_log(current_user: Optional[EmployeeUser | AdminUser] = None) -> str:
    """
    Get user name for activity logging.
    Returns actual user name if authenticated, otherwise returns 'System'
    """
    if current_user:
        return current_user.name if hasattr(current_user, 'name') else current_user.email
    return "System"

def get_user_type_for_log(current_user: Optional[EmployeeUser | AdminUser] = None) -> str:
    """
    Get user type for activity logging.
    Returns actual user role if authenticated, otherwise returns 'System'
    """
    if current_user:
        if isinstance(current_user, AdminUser):
            return "Admin"
        elif hasattr(current_user, 'role'):
            return current_user.role
    return "System"
