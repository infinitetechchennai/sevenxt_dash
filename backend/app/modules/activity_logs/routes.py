from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app.modules.auth.routes import get_current_employee
from .service import (
    get_activity_logs,
    get_activity_log_by_id,
    get_user_activity_logs,
    get_activity_stats
)
from .schemas import ActivityLogResponse
import csv
from io import StringIO
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


@router.get("", response_model=List[ActivityLogResponse], include_in_schema=False)
@router.get("/", response_model=List[ActivityLogResponse])
def list_activity_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_type: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_employee)
):
    """
    Get activity logs with optional filters.
    Only accessible by Admin users.
    """
    # Parse dates if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    logs = get_activity_logs(
        db=db,
        skip=skip,
        limit=limit,
        user_type=user_type,
        module=module,
        status=status,
        search=search,
        start_date=start_dt,
        end_date=end_dt
    )
    
    return logs


@router.get("/stats")
def get_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Get activity statistics for the specified number of days.
    """
    return get_activity_stats(db=db, days=days)


@router.get("/user/{user_id}", response_model=List[ActivityLogResponse])
def get_user_logs(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get activity logs for a specific user.
    """
    logs = get_user_activity_logs(db=db, user_id=user_id, limit=limit)
    return logs


@router.get("/export")
def export_activity_logs(
    user_type: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Export activity logs as CSV.
    """
    # Parse dates if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    logs = get_activity_logs(
        db=db,
        skip=0,
        limit=10000,  # Export up to 10k records
        user_type=user_type,
        module=module,
        status=status,
        search=search,
        start_date=start_dt,
        end_date=end_dt
    )
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'User Name', 'User Type', 'Action', 'Module', 
        'Details', 'Status', 'IP Address', 'Timestamp'
    ])
    
    # Write data
    for log in logs:
        writer.writerow([
            log.id,
            log.user_name or 'System',
            log.user_type or 'N/A',
            log.action,
            log.module,
            log.details or '',
            log.status.value if log.status else 'Success',
            log.ip_address or '',
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else ''
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=activity_logs.csv"}
    )


@router.get("/{log_id}", response_model=ActivityLogResponse)
def get_log_detail(
    log_id: int,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific activity log.
    """
    log = get_activity_log_by_id(db=db, log_id=log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Activity log not found")
    return log
