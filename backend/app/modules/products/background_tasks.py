import asyncio
from datetime import datetime
from app.database import SessionLocal
from app.modules.products import models

async def check_expired_offers():
    """
    Background task that runs every minute to check and expire offers.
    """
    while True:
        try:
            db = SessionLocal()
            now = datetime.now()
            
            # Find all products with expired offers
            products = db.query(models.Product).filter(
                (models.Product.b2c_offer_end_date != None) | 
                (models.Product.b2b_offer_end_date != None)
            ).all()
            
            expired_count = 0
            for product in products:
                changed = False
                
                # Check B2C offer expiration
                b2c_end_date = product.b2c_offer_end_date
                if isinstance(b2c_end_date, str):
                    try:
                        b2c_end_date = datetime.fromisoformat(b2c_end_date.replace('Z', '+00:00'))
                    except:
                        pass

                if b2c_end_date and isinstance(b2c_end_date, datetime) and b2c_end_date < now:
                    print(f"Expiring B2C offer for product: {product.name}")
                    product.b2c_active_offer = 0.0
                    product.b2c_discount = 0.0
                    product.b2c_offer_price = 0.0
                    product.b2c_offer_start_date = None
                    product.b2c_offer_end_date = None
                    changed = True
                    expired_count += 1
                
                # Check B2B offer expiration
                b2b_end_date = product.b2b_offer_end_date
                if isinstance(b2b_end_date, str):
                    try:
                        b2b_end_date = datetime.fromisoformat(b2b_end_date.replace('Z', '+00:00'))
                    except:
                        pass

                if b2b_end_date and isinstance(b2b_end_date, datetime) and b2b_end_date < now:
                    print(f"Expiring B2B offer for product: {product.name}")
                    product.b2b_active_offer = 0.0
                    product.b2b_discount = 0.0
                    product.b2b_offer_price = 0.0
                    product.b2b_offer_start_date = None
                    product.b2b_offer_end_date = None
                    changed = True
                    expired_count += 1
                
                if changed:
                    db.add(product)
            
            if expired_count > 0:
                db.commit()
                print(f"✅ Expired {expired_count} offers")
            
            db.close()
            
        except Exception as e:
            print(f"Error in background task: {e}")
            import traceback
            traceback.print_exc()
        
        # Wait 60 seconds before next check
        await asyncio.sleep(60)
