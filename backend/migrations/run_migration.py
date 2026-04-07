"""
Database migration script to add address and permissions fields to users table
"""
import mysql.connector
from mysql.connector import Error
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

def run_migration():
    """Run the database migration to add new columns"""
    try:
        # Connect to MySQL database
        connection = mysql.connector.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            print(f"Connected to MySQL database: {settings.DB_NAME}")
            
            # Check if columns already exist
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME IN ('address', 'city', 'state', 'pincode', 'permissions', 'last_login', 'created_at', 'updated_at', 'deleted_at')
            """, (settings.DB_NAME,))
            
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            if len(existing_columns) == 9:
                print("[OK] All columns already exist. Migration not needed.")
                return True
            
            print(f"Found {len(existing_columns)} existing columns. Adding missing columns...")
            
            # Add address column if not exists
            if 'address' not in existing_columns:
                print("Adding 'address' column...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN address TEXT NULL AFTER status
                """)
                print("[OK] Added 'address' column")
            
            # Add city column if not exists
            if 'city' not in existing_columns:
                print("Adding 'city' column...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN city VARCHAR(100) NULL AFTER address
                """)
                print("[OK] Added 'city' column")
            
            # Add state column if not exists
            if 'state' not in existing_columns:
                print("Adding 'state' column...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN state VARCHAR(100) NULL AFTER city
                """)
                print("[OK] Added 'state' column")
            
            # Add pincode column if not exists
            if 'pincode' not in existing_columns:
                print("Adding 'pincode' column...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN pincode VARCHAR(20) NULL AFTER state
                """)
                print("[OK] Added 'pincode' column")
            
            # Add permissions column if not exists
            if 'permissions' not in existing_columns:
                print("Adding 'permissions' column...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN permissions JSON NULL AFTER pincode
                """)
                print("[OK] Added 'permissions' column")

            # Add last_login column if not exists
            if 'last_login' not in existing_columns:
                print("Adding 'last_login' column...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN last_login DATETIME NULL
                """)
                print("[OK] Added 'last_login' column")

            # Add created_at column if not exists
            if 'created_at' not in existing_columns:
                print("Adding 'created_at' column...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
                print("[OK] Added 'created_at' column")

            # Add updated_at column if not exists
            if 'updated_at' not in existing_columns:
                print("Adding 'updated_at' column...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                """)
                print("[OK] Added 'updated_at' column")

            # Add deleted_at column if not exists
            if 'deleted_at' not in existing_columns:
                print("Adding 'deleted_at' column...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN deleted_at DATETIME NULL
                """)
                print("[OK] Added 'deleted_at' column")
            
            connection.commit()
            print("\n[SUCCESS] Migration completed successfully!")
            
            # Show updated table structure
            cursor.execute("DESCRIBE users")
            print("\nUpdated table structure:")
            print("-" * 80)
            for row in cursor.fetchall():
                print(f"{row[0]:<20} {row[1]:<20} {row[2]:<10} {row[3]:<10}")
            print("-" * 80)
            
            return True
            
    except Error as e:
        print(f"[ERROR] Error during migration: {e}")
        return False
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    print("=" * 80)
    print("Running Database Migration: Add Address and Permissions Fields")
    print("=" * 80)
    print()
    
    success = run_migration()
    
    if success:
        print("\n[SUCCESS] Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n[ERROR] Migration failed!")
        sys.exit(1)
