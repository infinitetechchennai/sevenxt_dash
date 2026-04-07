from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from .models import ActivityLog, ActivityStatus
from .schemas import ActivityLogCreate
from fastapi import Request


def log_activity(
    db: Session,
    action: str,
    module: str,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    user_type: Optional[str] = None,
    details: Optional[str] = None,
    status: str = "Success",
    affected_entity_type: Optional[str] = None,
    affected_entity_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    request: Optional[Request] = None
):
    """
    Helper function to log activity to the database.
    Can be called from any route to track user actions.
    """
    # Get IP address from request if not provided
    if request and not ip_address:
        ip_address = request.client.host if request.client else None
    
    # Map status string to enum
    status_enum = ActivityStatus.SUCCESS
    if status.lower() == "failed":
        status_enum = ActivityStatus.FAILED
    elif status.lower() == "warning":
        status_enum = ActivityStatus.WARNING
    
    activity_log = ActivityLog(
        user_id=user_id,
        user_name=user_name,
        user_type=user_type,
        action=action,
        module=module,
        details=details,
        ip_address=ip_address,
        status=status_enum,
        affected_entity_type=affected_entity_type,
        affected_entity_id=affected_entity_id
    )
    
    db.add(activity_log)
    db.commit()
    db.refresh(activity_log)
    
    return activity_log


def get_activity_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_type: Optional[str] = None,
    module: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[ActivityLog]:
    """
    Retrieve activity logs with optional filters.
    """
    query = db.query(ActivityLog)
    
    # Apply filters
    if user_type:
        query = query.filter(ActivityLog.user_type == user_type)
    
    if module:
        query = query.filter(ActivityLog.module == module)
    
    if status:
        query = query.filter(ActivityLog.status == status)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (ActivityLog.user_name.ilike(search_pattern)) |
            (ActivityLog.action.ilike(search_pattern)) |
            (ActivityLog.details.ilike(search_pattern))
        )
    
    if start_date:
        query = query.filter(ActivityLog.timestamp >= start_date)
    
    if end_date:
        query = query.filter(ActivityLog.timestamp <= end_date)
    
    # Order by most recent first
    query = query.order_by(ActivityLog.timestamp.desc())
    
    # Apply pagination
    logs = query.offset(skip).limit(limit).all()
    
    return logs


def get_activity_log_by_id(db: Session, log_id: int) -> Optional[ActivityLog]:
    """
    Get a specific activity log by ID.
    """
    return db.query(ActivityLog).filter(ActivityLog.id == log_id).first()


def get_user_activity_logs(
    db: Session,
    user_id: str,
    limit: int = 50
) -> List[ActivityLog]:
    """
    Get activity logs for a specific user.
    """
    return db.query(ActivityLog)\
        .filter(ActivityLog.user_id == user_id)\
        .order_by(ActivityLog.timestamp.desc())\
        .limit(limit)\
        .all()


def get_activity_stats(db: Session, days: int = 7):
    """
    Get activity statistics for the dashboard.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    total_activities = db.query(ActivityLog)\
        .filter(ActivityLog.timestamp >= start_date)\
        .count()
    
    successful = db.query(ActivityLog)\
        .filter(ActivityLog.timestamp >= start_date)\
        .filter(ActivityLog.status == ActivityStatus.SUCCESS)\
        .count()
    
    failed = db.query(ActivityLog)\
        .filter(ActivityLog.timestamp >= start_date)\
        .filter(ActivityLog.status == ActivityStatus.FAILED)\
        .count()
    
    return {
        "total_activities": total_activities,
        "successful": successful,
        "failed": failed,
        "period_days": days
    }
