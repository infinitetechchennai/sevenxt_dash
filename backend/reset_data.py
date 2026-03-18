
from sqlalchemy import create_engine, text
import json
import random
from datetime import datetime, timedelta

# Database Connection (Same as used before)
DB_URL = "postgresql://postgres:Inno%40123@localhost/sevennxt_db"

def reset_and_seed_data():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print("1. Cleaning up existing data related to Products and Orders...")
            # Disable constraints momentarily or delete in order
            conn.execute(text("DELETE FROM public.product_variants;"))
            conn.execute(text("DELETE FROM public.product_attributes;"))
            conn.execute(text("DELETE FROM public.orders;"))
            conn.execute(text("DELETE FROM public.products;"))
            print("   Tables cleared.")

            print("2. Inserting New Common Products...")
            
            # Products Data
            products = [
                {
                    "id": "prod_dslr_001",
                    "name": "Nikon Z9 Mirrorless Camera",
                    "category": "Camera",
                    "price": 450000.00,
                    "stock": 15,
                    "image": "https://placehold.co/600x400?text=Nikon+Z9"
                },
                {
                    "id": "prod_lens_002",
                    "name": "Sony FE 24-70mm GM II",
                    "category": "Lens",
                    "price": 189990.00,
                    "stock": 25,
                    "image": "https://placehold.co/600x400?text=Sony+Lens"
                },
                {
                    "id": "prod_drone_003",
                    "name": "DJI Mavic 3 Pro",
                    "category": "Drone",
                    "price": 225000.00,
                    "stock": 8,
                    "image": "https://placehold.co/600x400?text=DJI+Mavic"
                },
                {
                    "id": "prod_tripod_004",
                    "name": "Manfrotto Carbon Tripod",
                    "category": "Accessory",
                    "price": 35000.00,
                    "stock": 50,
                    "image": "https://placehold.co/600x400?text=Tripod"
                },
                 {
                    "id": "prod_mic_005",
                    "name": "Rode Wireless Pro",
                    "category": "Audio",
                    "price": 42000.00,
                    "stock": 30,
                    "image": "https://placehold.co/600x400?text=Rode+Mic"
                }
            ]

            for p in products:
                # Insert into Products Table
                # Note: b2c_price is used as the main price here
                q_prod = text("""
                INSERT INTO public.products (id, name, category, b2c_price, stock, status, image, created_at, updated_at)
                VALUES (:id, :name, :category, :price, :stock, 'Published', :image, NOW(), NOW())
                """)
                conn.execute(q_prod, p)
            
            print("   Products inserted.")

            print("3. Inserting Orders linked to these Products...")
            
            # Orders Data (Generating 10 random orders using the above products)
            statuses = ['Pending', 'Confirmed', 'AWB_GENERATED', 'Shipped', 'Delivered']
            payments = ['Prepaid', 'COD', 'razorpay']
            
            # Helper to create order
            def create_order(oid_int, order_id_str, prod_ref, qty, cust_name):
                # Calculate total
                price = prod_ref['price']
                total = price * qty
                
                # Product JSON for Order
                # Vital: Ensure this matches what frontend expects for Reports
                prod_json = [{
                    "id": prod_ref['id'],
                    "name": prod_ref['name'],
                    "price": str(price), # Frontend often expects string in JSON
                    "quantity": qty,
                    "image": prod_ref['image']
                }]
                
                # Random Date (last 30 days)
                days_ago = random.randint(0, 30)
                date_val = datetime.now() - timedelta(days=days_ago)

                params = {
                    "id": oid_int,
                    "order_id": order_id_str,
                    "amount": total,
                    "status": random.choice(statuses),
                    "payment": random.choice(payments),
                    "customer_name": cust_name,
                    "products": json.dumps(prod_json),
                    "phone": "9999999999",
                    "email": "customer@example.com",
                    "state": "Maharashtra",
                    "date": date_val
                }
                
                q_order = text("""
                INSERT INTO public.orders (
                    id, order_id, amount, status, payment, customer_name, products, created_at, updated_at, phone, email, state
                ) VALUES (
                    :id, :order_id, :amount, :status, :payment, :customer_name, :products, :date, :date, :phone, :email, :state
                )
                """)
                conn.execute(q_order, params)

            # Manually creating some diverse orders
            # Order 1: Nikon Z9
            create_order(1001, "ORD-2026-001", products[0], 1, "Rahul Sharma")
            # Order 2: Sony Lens
            create_order(1002, "ORD-2026-002", products[1], 1, "Sneha Gupta")
             # Order 3: 2x Rode Mics
            create_order(1003, "ORD-2026-003", products[4], 2, "Vlog Studio")
             # Order 4: DJI Drone
            create_order(1004, "ORD-2026-004", products[2], 1, "Aerial Shots Ltd")
             # Order 5: Another Nikon Z9
            create_order(1005, "ORD-2026-005", products[0], 1, "Wildlife Pro")
             # Order 6: Tripod
            create_order(1006, "ORD-2026-006", products[3], 3, "Film School")
            # Order 7: Sony Lens
            create_order(1007, "ORD-2026-007", products[1], 1, "Wedding Cam")
            
            
            conn.commit()
            print("   Orders inserted.")
            print("Done. Database has been reset with consistent data.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reset_and_seed_data()
