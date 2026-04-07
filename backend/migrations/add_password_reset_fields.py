"""
Migration script to add password reset fields to employee_users table
Run this script to add reset_token and reset_token_expires columns
"""

import pymysql
import os

def run_migration():
    """Add password reset fields to employee_users table"""
    
    # Database configuration (update these if needed)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "sevenext")
    
    try:
        # Connect to database
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print(f"✅ Connected to database: {DB_NAME}")
        
        with connection.cursor() as cursor:
            # Check if columns already exist
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = 'employee_users'
                AND COLUMN_NAME IN ('reset_token', 'reset_token_expires')
            """, (DB_NAME,))
            
            result = cursor.fetchone()
            
            if result['count'] > 0:
                print("⚠️  Password reset columns already exist. Skipping migration.")
                return
            
            # Add reset_token column
            print("📝 Adding reset_token column...")
            cursor.execute("""
                ALTER TABLE employee_users
                ADD COLUMN reset_token VARCHAR(255) NULL AFTER permissions
            """)
            
            # Add reset_token_expires column
            print("📝 Adding reset_token_expires column...")
            cursor.execute("""
                ALTER TABLE employee_users
                ADD COLUMN reset_token_expires DATETIME NULL AFTER reset_token
            """)
            
            connection.commit()
            print("✅ Migration completed successfully!")
            print("   - Added: reset_token (VARCHAR 255)")
            print("   - Added: reset_token_expires (DATETIME)")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        connection.close()

if __name__ == "__main__":
    print("=" * 50)
    print("Running Password Reset Migration")
    print("=" * 50)
    run_migration()
    print("=" * 50)

