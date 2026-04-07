import razorpay
from sqlalchemy.orm import Session
from .models import Coupon
from app.config import settings
from datetime import datetime
from app.modules.products.models import Product

# Initialize Razorpay Client
rzp_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def get_coupons(db: Session):
    return db.query(Coupon).order_by(Coupon.id.desc()).all()

def create_coupon(db: Session, payload: any):
    rzp_id = None
    try:
        # 1. Syncing with Razorpay
        offer_data = {
            "name": f"Coupon {payload.code}",
            "display_name": f"{payload.value} Off",
            "type": "discount",
            "payment_method": "all"
        }
        if payload.type == "Percentage":
            offer_data["percentage"] = int(float(payload.value))
        else:
            offer_data["amount"] = int(float(payload.value) * 100) # Paise

        rzp_offer = rzp_client.offer.create(data=offer_data)
        rzp_id = rzp_offer.get("id")
    except Exception as e:
        print(f"Razorpay Sync Error: {e}")

    # 2. Save to Local DB
    coupon = Coupon(
        code=payload.code,
        type=payload.type,
        value=payload.value,
        target=payload.target,
        usage_count=f"0/{payload.usage_limit}",
        status="Active",
        expiry=payload.expiry,
        min_order_value=payload.min_order_value,
        usage_limit=payload.usage_limit,
        razorpay_offer_id=rzp_id
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon

def update_coupon(db: Session, coupon_id: int, payload):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon: return None
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(coupon, field, value)
    db.commit()
    db.refresh(coupon)
    return coupon

def delete_coupon(db: Session, coupon_id: int):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon: return False
    db.delete(coupon)
    db.commit()
    return True

def get_flash_deals_from_products(db):
    # Flash Deals workflow untouched
    now = datetime.now()
    products = db.query(Product).filter(
        Product.b2c_active_offer > 0,
        Product.b2c_offer_price > 0,
        Product.b2c_offer_start_date != None,
        Product.b2c_offer_end_date != None,
        Product.b2c_offer_start_date <= now,
        Product.b2c_offer_end_date >= now
    ).all()

    flash_deals = []
    for p in products:
        flash_deals.append({
            "id": p.id,
            "product": p.name,
            "original_price": p.b2c_price,
            "deal_price": p.b2c_offer_price,
            "discount": f"{int(p.b2c_active_offer)}%",
            "ends_in": p.b2c_offer_end_date.isoformat(),
            "status": "Active",
            "target": "B2C"
        })
    return flash_deals