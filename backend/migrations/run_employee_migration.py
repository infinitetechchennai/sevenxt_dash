"""
Database migration script to setup employee_users table
"""
import mysql.connector
from mysql.connector import Error
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def run_migration():
    """Run the database migration to setup employee_users table"""
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
            
            # Check if employee_users table exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'employee_users'
            """, (settings.DB_NAME,))
            
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                print("Creating employee_users table...")
                cursor.execute("""
                    CREATE TABLE employee_users (
                        id INT(11) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(150) NOT NULL UNIQUE,
                        password VARCHAR(255) NOT NULL,
                        role ENUM('admin', 'staff', 'super_admin') NOT NULL DEFAULT 'staff',
                        status ENUM('active', 'inactive', 'blocked') NOT NULL DEFAULT 'active',
                        address TEXT NULL,
                        city VARCHAR(100) NULL,
                        state VARCHAR(100) NULL,
                        pincode VARCHAR(20) NULL,
                        permissions JSON NULL,
                        phone VARCHAR(15) NULL,
                        last_login DATETIME NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        deleted_at TIMESTAMP NULL,
                        INDEX idx_email (email),
                        INDEX idx_role (role),
                        INDEX idx_status (status)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                print("[OK] Created employee_users table")
            else:
                print("[OK] employee_users table already exists")
                
                # Check and add missing columns
                cursor.execute("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = %s 
                    AND TABLE_NAME = 'employee_users'
                """, (settings.DB_NAME,))
                
                existing_columns = [row[0] for row in cursor.fetchall()]
                
                # Add address if not exists
                if 'address' not in existing_columns:
                    print("Adding 'address' column...")
                    cursor.execute("ALTER TABLE employee_users ADD COLUMN address TEXT NULL AFTER status")
                    print("[OK] Added 'address' column")
                
                # Add city if not exists
                if 'city' not in existing_columns:
                    print("Adding 'city' column...")
                    cursor.execute("ALTER TABLE employee_users ADD COLUMN city VARCHAR(100) NULL AFTER address")
                    print("[OK] Added 'city' column")
                
                # Add state if not exists
                if 'state' not in existing_columns:
                    print("Adding 'state' column...")
                    cursor.execute("ALTER TABLE employee_users ADD COLUMN state VARCHAR(100) NULL AFTER city")
                    print("[OK] Added 'state' column")
                
                # Add pincode if not exists
                if 'pincode' not in existing_columns:
                    print("Adding 'pincode' column...")
                    cursor.execute("ALTER TABLE employee_users ADD COLUMN pincode VARCHAR(20) NULL AFTER state")
                    print("[OK] Added 'pincode' column")
                
                # Add permissions if not exists
                if 'permissions' not in existing_columns:
                    print("Adding 'permissions' column...")
                    cursor.execute("ALTER TABLE employee_users ADD COLUMN permissions JSON NULL AFTER pincode")
                    print("[OK] Added 'permissions' column")
            
            connection.commit()
            print("\n[SUCCESS] Migration completed successfully!")
            
            # Show table structure
            cursor.execute("DESCRIBE employee_users")
            print("\nEmployee Users table structure:")
            print("-" * 80)
            for row in cursor.fetchall():
                print(f"{row[0]:<20} {row[1]:<30} {row[2]:<10}")
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
    print("Running Database Migration: Setup Employee Users Table")
    print("=" * 80)
    print()
    
    success = run_migration()
    
    if success:
        print("\n[SUCCESS] Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n[ERROR] Migration failed!")
        sys.exit(1)
