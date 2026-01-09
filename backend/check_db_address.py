import psycopg2

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="sevenext",
    user="postgres",
    password="12345"
)

cursor = conn.cursor()

print("\n" + "="*80)
print("CHECKING ADDRESS DATA IN DATABASE TABLES")
print("="*80 + "\n")

# Check admin_users table
print("📋 ADMIN_USERS Table:")
print("-" * 80)
cursor.execute("""
    SELECT id, name, email, role, address, city, state, pincode 
    FROM admin_users 
    WHERE deleted_at IS NULL
""")
admins = cursor.fetchall()

if admins:
    for admin in admins:
        print(f"\n👤 ID: {admin[0]}")
        print(f"   Name: {admin[1]}")
        print(f"   Email: {admin[2]}")
        print(f"   Role: {admin[3]}")
        print(f"   Address: {admin[4] or '❌ NULL/EMPTY'}")
        print(f"   City: {admin[5] or '❌ NULL/EMPTY'}")
        print(f"   State: {admin[6] or '❌ NULL/EMPTY'}")
        print(f"   Pincode: {admin[7] or '❌ NULL/EMPTY'}")
else:
    print("   ⚠️  No admin users found")

# Check employee_users table
print("\n📋 EMPLOYEE_USERS Table:")
print("-" * 80)
cursor.execute("""
    SELECT id, name, email, role, address, city, state, pincode 
    FROM employee_users 
    WHERE deleted_at IS NULL
""")
employees = cursor.fetchall()

if employees:
    for emp in employees:
        print(f"\n👤 ID: {emp[0]}")
        print(f"   Name: {emp[1]}")
        print(f"   Email: {emp[2]}")
        print(f"   Role: {emp[3]}")
        print(f"   Address: {emp[4] or '❌ NULL/EMPTY'}")
        print(f"   City: {emp[5] or '❌ NULL/EMPTY'}")
        print(f"   State: {emp[6] or '❌ NULL/EMPTY'}")
        print(f"   Pincode: {emp[7] or '❌ NULL/EMPTY'}")
else:
    print("   ⚠️  No employee users found")

print("\n" + "="*80)
print("✅ Database check complete!")
print("="*80 + "\n")

cursor.close()
conn.close()
