from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from .service import DashboardService
from .schemas import DashboardOverviewResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/overview", response_model=DashboardOverviewResponse)
def get_overview(
    timeframe: str = Query("Monthly"),
    db: Session = Depends(get_db)
):
    return DashboardService.get_overview_data(db, timeframe)