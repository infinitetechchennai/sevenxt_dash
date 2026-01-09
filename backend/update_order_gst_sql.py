from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    target_awb = "84927910001164"
    
    # Check if order exists
    sql_check = text("SELECT id, order_id, sgst_percentage FROM orders WHERE awb_number = :awb")
    result = db.execute(sql_check, {"awb": target_awb}).fetchone()
    
    if result:
        print(f"Found order: {result[1]}, Current SGST: {result[2]}")
        
        # Update
        sql_update = text("UPDATE orders SET sgst_percentage = 9.0, cgst_percentage = 9.0 WHERE awb_number = :awb")
        db.execute(sql_update, {"awb": target_awb})
        db.commit()
        print("✅ Updated GST for the order.")
    else:
        print("❌ Order not found by AWB.")
        # Fallback to amount 1000
        sql_fallback = text("UPDATE orders SET sgst_percentage = 9.0, cgst_percentage = 9.0 WHERE amount = 1000")
        res = db.execute(sql_fallback)
        db.commit()
        print(f"✅ Updated {res.rowcount} orders with amount 1000.")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
