from sqlalchemy import text
from app.database import engine
import json

with engine.connect() as conn:
    result = conn.execute(text("SELECT order_id, amount, products FROM orders WHERE order_id = 'ORD-2026-001'"))
    row = result.first()
    
    if row:
        print(f"Order: {row.order_id}")
        print(f"Amount: ₹{row.amount}")
        print(f"Products JSON: {row.products}")
        print(f"\nProducts Type: {type(row.products)}")
        
        if row.products:
            try:
                if isinstance(row.products, str):
                    products = json.loads(row.products)
                else:
                    products = row.products
                    
                print(f"\nParsed Products ({len(products)} items):")
                for i, p in enumerate(products, 1):
                    print(f"\n  Product {i}:")
                    for key, value in p.items():
                        print(f"    {key}: {value} (type: {type(value).__name__})")
            except Exception as e:
                print(f"\nERROR parsing: {e}")
        else:
            print("\n⚠️  Products is NULL or empty!")
    else:
        print("Order not found!")
