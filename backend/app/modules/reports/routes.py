from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
# 1. Update this import to include the 's'
from .service import ReportsService 

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/sales")
def get_sales(timeframe: str = "daily", db: Session = Depends(get_db)):
    # 2. Update the class name here
    return ReportsService.get_sales_report(db, timeframe)

@router.get("/top-products")
def get_products(db: Session = Depends(get_db)):
    # 3. Update the class name here
    # Note: Using get_sales_report(db, 'all') because it contains top_products
    data = ReportsService.get_sales_report(db, "all")
    return data.get("top_products", [])

@router.get("/delivery")
def get_delivery(db: Session = Depends(get_db)):
    return ReportsService.get_delivery_stats(db)

@router.get("/segments")
def get_segments(db: Session = Depends(get_db)):
    return ReportsService.get_segment_analysis(db)

@router.get("/returns")
def get_returns(db: Session = Depends(get_db)):
    return ReportsService.get_return_analysis(db)

@router.get("/growth")
def get_growth(db: Session = Depends(get_db)):
    return ReportsService.get_growth_metrics(db)

@router.get("/payment-mix")
def get_payment_mix(db: Session = Depends(get_db)):
    return ReportsService.get_payment_stats(db)

@router.get("/geo")
def get_geo(db: Session = Depends(get_db)):
    return ReportsService.get_geo_stats(db)

@router.get("/sales-inventory")
def get_inventory(db: Session = Depends(get_db)):
    return ReportsService.get_sales_inventory(db)

@router.get("/sales-details")
def get_sales_details_route(db: Session = Depends(get_db)):
    return ReportsService.get_sales_details(db)

@router.get("/all")
def get_all_reports_route(db: Session = Depends(get_db)):
    return ReportsService.get_all_reports(db)
