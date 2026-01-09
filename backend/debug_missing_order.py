from sqlalchemy import text
from app.database import engine
import json

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            id,
            order_id, 
            amount,
            products::text as products_text
        FROM orders
        ORDER BY id
    """))
    
    print("📋 DETAILED ORDER ANALYSIS:\n")
    for row in result:
        print(f"Order ID: {row.order_id}")
        print(f"Amount: ₹{row.amount}")
        print(f"Products JSON: {row.products_text}")
        
        # Try to parse and show each product
        try:
            products = json.loads(row.products_text)
            print(f"Number of products: {len(products)}")
            for i, p in enumerate(products, 1):
                print(f"  Product {i}:")
                print(f"    Name: {p.get('name', 'MISSING')}")
                print(f"    Price: {p.get('price', 'MISSING')}")
                print(f"    Quantity: {p.get('quantity', 'MISSING')}")
                print(f"    Product ID: {p.get('product_id', 'MISSING')}")
        except Exception as e:
            print(f"  ERROR parsing products: {e}")
        
        print("-" * 60)
