
from sqlalchemy import create_engine, text

# Using the connection string inferred from the user's environment or defaults
# If this fails, I'll ask for credentials, but usually localhost postgres is standard
DB_URL = "postgresql://postgres:Inno%40123@localhost/sevennxt_db"

def insert_dummy_data():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # Added 'phone' and 'email' fields to satisfy constraints
            queries = [
                """
                INSERT INTO public.orders (
                    id, order_id, amount, status, payment, customer_name, products, created_at, updated_at, phone, email, state
                ) 
                VALUES (
                    'ord_demo_fixed_01', 
                    'ORD-2026-FIX-01', 
                    85000.00, 
                    'AWB_GENERATED', 
                    'Prepaid', 
                    'Tech User', 
                    '[{"id": "prod_iphone15", "name": "iPhone 15", "price": "85000", "quantity": 1}]', 
                    NOW(), 
                    NOW(),
                    '9876543210',
                    'user@example.com',
                    'Maharashtra'
                );
                """,
                 """
                INSERT INTO public.orders (
                    id, order_id, amount, status, payment, customer_name, products, created_at, updated_at, phone, email, state
                ) 
                VALUES (
                    'ord_demo_fixed_02', 
                    'ORD-2026-FIX-02', 
                    1200.00, 
                    'Pending', 
                    'COD', 
                    'Demo User', 
                    '[{"id": "prod_tshirt", "name": "Cotton T-Shirt", "price": "1200", "quantity": 1}]', 
                    NOW(), 
                    NOW(),
                    '9123456789',
                    'demo@example.com',
                    'Delhi'
                );
                """
            ]
            
            for q in queries:
                try:
                    conn.execute(text(q))
                    print("Inserted order successfully.")
                except Exception as inner_e:
                    print(f"Skipping duplicate or error: {inner_e}")
            
            conn.commit()
            print("Done.")
    except Exception as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    insert_dummy_data()
