"""
Script to check existing products and help update orders with correct product IDs
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
import json

# Create database session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Import models after session is created
from app.modules.products.models import Product
from app.modules.orders.models import Order

print("=" * 80)
print("EXISTING PRODUCTS IN DATABASE")
print("=" * 80)

products = db.query(Product).limit(20).all()

if not products:
    print("❌ NO PRODUCTS FOUND IN DATABASE!")
    print("\nYou need to add products first before orders can reference them.")
else:
    print(f"\nFound {len(products)} products:\n")
    for p in products:
        print(f"ID: {p.id:20s} | Name: {p.name:40s} | HSN: {p.hsn or 'N/A'}")

print("\n" + "=" * 80)
print("EXISTING ORDERS IN DATABASE")
print("=" * 80)

orders = db.query(Order).limit(10).all()

if not orders:
    print("❌ NO ORDERS FOUND IN DATABASE!")
else:
    print(f"\nFound {len(orders)} orders:\n")
    for o in orders:
        products_data = o.products
        if isinstance(products_data, str):
            try:
                products_data = json.loads(products_data.replace("'", '"'))
            except:
                products_data = []
        
        print(f"\nOrder ID: {o.order_id}")
        print(f"Customer: {o.customer_name}")
        print(f"Products in order:")
        if isinstance(products_data, list):
            for item in products_data:
                if isinstance(item, dict):
                    prod_id = item.get('id') or item.get('product_id') or 'N/A'
                    prod_name = item.get('name') or item.get('product_name') or 'N/A'
                    print(f"  - ID: {prod_id:20s} | Name: {prod_name}")
        print("-" * 80)

print("\n" + "=" * 80)
print("SOLUTION")
print("=" * 80)

if products:
    print("\n✅ To fix the HSN issue, update your orders to use actual product IDs.")
    print("\nExample SQL to update an order:")
    print(f"""
UPDATE orders 
SET products = '[{{"id": "{products[0].id}", "name": "{products[0].name}", "quantity": 2, "price": {products[0].b2c_price}}}]'::json
WHERE order_id = 'ORD-2026-01';
""")
    
    print("\nOr create a new order with a real product:")
    print(f"""
INSERT INTO orders (
    order_id, customer_type, customer_name, products, amount, payment, status,
    address, email, phone, city, state, pincode
) VALUES (
    'ORD-TEST-001',
    'B2C',
    'Test Customer',
    '[{{"id": "{products[0].id}", "name": "{products[0].name}", "quantity": 1, "price": {products[0].b2c_price}}}]'::json,
    {products[0].b2c_price},
    'Paid',
    'Confirmed',
    '123 Test Street',
    'test@example.com',
    '+91 9876543210',
    'Chennai',
    'Tamil Nadu',
    '600001'
);
""")
else:
    print("\n❌ You need to add products to the database first!")
    print("\nGo to the Products page and add some products, then create orders referencing those products.")

db.close()
