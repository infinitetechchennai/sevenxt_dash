from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from . import service, schemas

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

@router.get("/coupons", response_model=list[schemas.CouponOut])
def list_coupons(db: Session = Depends(get_db)):
    return service.get_coupons(db)

@router.post("/coupons", response_model=schemas.CouponOut)
def add_coupon(payload: schemas.CouponCreate, db: Session = Depends(get_db)):
    # This now handles both DB save and Razorpay Sync
    return service.create_coupon(db, payload)

@router.put("/coupons/{coupon_id}", response_model=schemas.CouponOut)
def update_coupon(coupon_id: int, payload: schemas.CouponUpdate, db: Session = Depends(get_db)):
    coupon = service.update_coupon(db, coupon_id, payload)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return coupon

@router.delete("/coupons/{coupon_id}")
def delete_coupon(coupon_id: int, db: Session = Depends(get_db)):
    success = service.delete_coupon(db, coupon_id)
    if not success:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return {"message": "Coupon deleted"}

# FLASH DEALS ROUTE (UNTOUCHED)
@router.get("/flash-deals")
def list_flash_deals(db: Session = Depends(get_db)):
    return service.get_flash_deals_from_products(db)