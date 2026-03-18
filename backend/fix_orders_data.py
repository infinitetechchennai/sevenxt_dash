
from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:Inno%40123@localhost/sevennxt_db"

def fix_data():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # 1. Clean up string-ID dummy data that violates the integer schema
            try:
                # We can't query "id LIKE 'ord%'" if id column is mixed type, but in Postgres 
                # if the column is defined as String (VARCHAR) in DB but Int in Schema, we can store strings.
                # But to satisfy the schema (which requires Int), we must delete string rows.
                conn.execute(text("DELETE FROM public.orders WHERE id ~ '^ord_fix_';"))
                print("Deleted string-ID dummy orders.")
            except Exception as e:
                print(f"Cleanup warning: {e}")

            # 2. Insert Valid Integer ID Data
            queries = [
                 """
                INSERT INTO public.orders (
                    id, order_id, amount, status, payment, customer_name, products, created_at, updated_at, phone, email, state
                ) 
                VALUES (
                    '9001', 
                    'ORD-INT-901', 
                    79999.00, 
                    'AWB_GENERATED', 
                    'Prepaid', 
                    'John Integer', 
                    '[{"id": "prod_14", "name": "iPhone 14 Pro", "price": "79999", "quantity": 1}]', 
                    NOW(), 
                    NOW(),
                    '9876543210',
                    'john.int@example.com',
                    'Maharashtra'
                );
                """,
                 """
                INSERT INTO public.orders (
                    id, order_id, amount, status, payment, customer_name, products, created_at, updated_at, phone, email, state
                ) 
                VALUES (
                    '9002', 
                    'ORD-INT-902', 
                    1499.00, 
                    'AWB_GENERATED', 
                    'COD', 
                    'Jane Integer', 
                    '[{"id": "prod_case", "name": "Phone Case", "price": "1499", "quantity": 1}]', 
                    NOW(), 
                    NOW(),
                    '9123456789',
                    'jane.int@example.com',
                    'Delhi'
                );
                """
            ]
            
            for q in queries:
                try:
                    conn.execute(text(q))
                    print("Inserted integer-ID order successfully.")
                except Exception as inner_e:
                    print(f"Insert error: {inner_e}")
            
            conn.commit()
            print("Done.")
    except Exception as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    fix_data()
