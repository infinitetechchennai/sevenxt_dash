"""
User Management Utility
========================
This script helps you create, update, and manage user accounts for the SevenXT Admin Dashboard.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.modules.auth.models import EmployeeUser
from app.modules.auth.service import get_password_hash, verify_password
import sys

# Create database connection
<<<<<<< HEAD
DATABASE_URL = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}" if settings.DB_PASSWORD else f"postgresql+psycopg2://{settings.DB_USER}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
=======
DATABASE_URL = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}" if settings.DB_PASSWORD else f"mysql+pymysql://{settings.DB_USER}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
>>>>>>> origin/dev
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def list_all_users():
    """List all active users"""
    db = SessionLocal()
    try:
        users = db.query(EmployeeUser).filter(
            EmployeeUser.deleted_at.is_(None)
        ).all()
        
        print("\n" + "="*70)
        print("ALL ACTIVE USERS")
        print("="*70)
        
        for user in users:
            print(f"\nID: {user.id}")
            print(f"Name: {user.name}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Status: {user.status}")
            print("-" * 70)
            
        print(f"\nTotal Users: {len(users)}\n")
    finally:
        db.close()

def create_user(email, password, name, role="admin", status="active"):
    """Create a new user"""
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(EmployeeUser).filter(
            EmployeeUser.email == email,
            EmployeeUser.deleted_at.is_(None)
        ).first()
        
        if existing:
            print(f"❌ User with email '{email}' already exists!")
            return False
        
        # Create new user
        new_user = EmployeeUser(
            name=name,
            email=email,
            password=get_password_hash(password),
            role=role,
            status=status
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"\n✅ User created successfully!")
        print(f"   ID: {new_user.id}")
        print(f"   Name: {new_user.name}")
        print(f"   Email: {new_user.email}")
        print(f"   Role: {new_user.role}")
        print(f"   Status: {new_user.status}")
        print(f"\n   Login credentials:")
        print(f"   Email: {email}")
        print(f"   Password: {password}\n")
        
        return True
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def reset_password(email, new_password):
    """Reset a user's password"""
    db = SessionLocal()
    try:
        user = db.query(EmployeeUser).filter(
            EmployeeUser.email == email,
            EmployeeUser.deleted_at.is_(None)
        ).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found!")
            return False
        
        user.password = get_password_hash(new_password)
        db.commit()
        
        print(f"\n✅ Password reset successfully for {user.name} ({email})")
        print(f"   New password: {new_password}\n")
        
        return True
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def check_user(email, password):
    """Check if a user exists and verify password"""
    db = SessionLocal()
    try:
        user = db.query(EmployeeUser).filter(
            EmployeeUser.email == email,
            EmployeeUser.deleted_at.is_(None)
        ).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found!")
            return False
        
        print(f"\n✅ User found:")
        print(f"   ID: {user.id}")
        print(f"   Name: {user.name}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role}")
        print(f"   Status: {user.status}")
        
        is_valid = verify_password(password, user.password)
        
        if is_valid:
            print(f"\n✅ Password is CORRECT!\n")
        else:
            print(f"\n❌ Password is INCORRECT!\n")
        
        return is_valid
    finally:
        db.close()

def main():
    """Main menu"""
    print("\n" + "="*70)
    print("SEVENXT USER MANAGEMENT UTILITY")
    print("="*70)
    print("\n1. List all users")
    print("2. Create new user")
    print("3. Reset password")
    print("4. Check user credentials")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        list_all_users()
    elif choice == "2":
        print("\n--- Create New User ---")
        email = input("Email: ").strip()
        password = input("Password: ").strip()
        name = input("Name: ").strip()
        role = input("Role (admin/staff) [admin]: ").strip() or "admin"
        status = input("Status (active/inactive) [active]: ").strip() or "active"
        create_user(email, password, name, role, status)
    elif choice == "3":
        print("\n--- Reset Password ---")
        email = input("Email: ").strip()
        password = input("New Password: ").strip()
        reset_password(email, password)
    elif choice == "4":
        print("\n--- Check User Credentials ---")
        email = input("Email: ").strip()
        password = input("Password: ").strip()
        check_user(email, password)
    elif choice == "5":
        print("\nGoodbye!\n")
        sys.exit(0)
    else:
        print("\n❌ Invalid choice!\n")

if __name__ == "__main__":
    try:
        while True:
            main()
            input("\nPress Enter to continue...")
    except KeyboardInterrupt:
        print("\n\nGoodbye!\n")
        sys.exit(0)
