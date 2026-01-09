from sqlalchemy import text
from app.database import engine
import json

with engine.connect() as conn:
    result = conn.execute(text("SELECT id, order_id, amount, products FROM orders"))
    
    print("📋 ALL ORDERS:")
    for row in result:
        print(f"\nOrder {row.order_id}:")
        print(f"  Amount: ₹{row.amount}")
        print(f"  Products: {row.products}")
