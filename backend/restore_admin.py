
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

# DB Connection
DB_URL = "postgresql://postgres:Inno%40123@localhost/sevennxt_db"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def restore_admin():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # Hash the default password 'password' (or whatever you use)
            hashed_password = pwd_context.hash("password")
            
            # Check if admin exists
            result = conn.execute(text("SELECT email FROM public.users WHERE email = 'admin@sevennxt.com'"))
            if result.fetchone():
                print("Admin user already exists.")
            else:
                # Insert Admin User
                # Assuming 'users' table structure. Modify columns if needed (e.g. is_active, is_superuser)
                # If specific columns like phone/role are needed, I'll add them.
                # Based on previous contexts, usually it's id, email, password, full_name.
                
                # Let's try a safe insert assuming standard columns. 
                # If this fails, I'll check schema.
                
                # Generating a proper ID if needed or letting serial handle it.
                conn.execute(text("""
                    INSERT INTO public.users (email, hashed_password, full_name, is_active, role, created_at, updated_at) 
                    VALUES ('admin@sevennxt.com', :pwd, 'Super Admin', true, 'admin', NOW(), NOW())
                """), {"pwd": hashed_password})
                
                conn.commit()
                print("Admin user restored successfully.")
                
    except Exception as e:
        print(f"Error restoring admin: {e}")

if __name__ == "__main__":
    restore_admin()
