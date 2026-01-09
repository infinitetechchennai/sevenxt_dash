from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    # Count orders
    result = conn.execute(text("SELECT COUNT(*) as count FROM orders"))
    order_count = result.scalar()
    print(f"Total Orders in Database: {order_count}\n")
    
    # Get all order amounts
    result = conn.execute(text("SELECT order_id, amount FROM orders ORDER BY id"))
    print("All Orders:")
    total = 0
    for row in result:
        print(f"  {row.order_id}: ₹{row.amount}")
        total += float(row.amount)
    print(f"\nTotal Revenue: ₹{total:,.2f}")
