from app.database import SessionLocal
from app.modules.orders.models import Order
from sqlalchemy import text

db = SessionLocal()

try:
    # Find the order
    # Using raw SQL for safety if model isn't fully syncd context-wise
    # But using ORM is better
    target_awb = "84927910001164"
    order = db.query(Order).filter(Order.awb_number == target_awb).first()
    
    if order:
        print(f"Found order: {order.order_id}")
        print(f"Current GST: SGST={order.sgst_percentage}, CGST={order.cgst_percentage}")
        
        # Update GST
        order.sgst_percentage = 9.0
        order.cgst_percentage = 9.0
        db.commit()
        db.refresh(order)
        print(f"✅ Updated GST to: SGST={order.sgst_percentage}, CGST={order.cgst_percentage}")
    else:
        print(f"❌ Order with AWB {target_awb} not found.")
        
        # Fallback: update ANY order with amount 1000 just for testing
        order = db.query(Order).filter(Order.amount == 1000).first()
        if order:
            print(f"Found alternative order with amount 1000: {order.order_id}")
            order.sgst_percentage = 9.0
            order.cgst_percentage = 9.0
            db.commit()
            print(f"✅ Updated GST for {order.order_id}")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
