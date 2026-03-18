"""
Migration to add colors column to products table
"""
import sys
import os

# Add parent directory to path to import database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine

def run_migration():
    """Add colors column to products table"""
    
    migration_sql = """
    -- Add colors column to products table
    ALTER TABLE products 
    ADD COLUMN IF NOT EXISTS colors VARCHAR(255);
    """
    
    try:
        with engine.connect() as conn:
            print("🔄 Running migration: Add colors column to products table...")
            conn.execute(text(migration_sql))
            conn.commit()
            print("✅ Migration completed successfully!")
            print("   - Added 'colors' column to products table")
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
