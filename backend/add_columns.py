import sys
sys.path.insert(0, '.')

from app.database import engine
from sqlalchemy import text

print("Adding delivery_attempts columns to exchanges table...")

try:
    with engine.connect() as conn:
        # Add delivery_attempts column
        conn.execute(text("""
            ALTER TABLE exchanges 
            ADD COLUMN IF NOT EXISTS delivery_attempts INTEGER DEFAULT 0
        """))
        print("✅ Added delivery_attempts column")
        
        # Add new_delivery_attempts column
        conn.execute(text("""
            ALTER TABLE exchanges 
            ADD COLUMN IF NOT EXISTS new_delivery_attempts INTEGER DEFAULT 0
        """))
        print("✅ Added new_delivery_attempts column")
        
        # Update existing rows
        conn.execute(text("""
            UPDATE exchanges 
            SET delivery_attempts = 0 
            WHERE delivery_attempts IS NULL
        """))
        
        conn.execute(text("""
            UPDATE exchanges 
            SET new_delivery_attempts = 0 
            WHERE new_delivery_attempts IS NULL
        """))
        print("✅ Updated existing rows")
        
        conn.commit()
        print("\n🎉 SUCCESS! Columns added successfully!")
        print("\nNow restart your backend server and test the webhook again.")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPlease run the SQL manually using pgAdmin or your database tool.")
