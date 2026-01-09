from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # Check total deliveries
    result = conn.execute(text("SELECT COUNT(*) as total FROM deliveries"))
    total = result.scalar()
    print(f"Total deliveries: {total}")
    
    # Check by status
    result = conn.execute(text("SELECT delivery_status, COUNT(*) as count FROM deliveries GROUP BY delivery_status"))
    print("\nDelivery Status Breakdown:")
    for row in result:
        print(f"  {row.delivery_status}: {row.count}")
    
    # Check what the dashboard query returns
    result = conn.execute(text("""
        SELECT 
            COUNT(CASE WHEN delivery_status IN ('Delivered', 'Completed') THEN 1 END)::int as delivered,
            COUNT(CASE WHEN delivery_status IN ('Pending', 'In Transit', 'Ready to Pickup') THEN 1 END)::int as pending,
            COUNT(*)::int as total
        FROM deliveries
        WHERE created_at >= NOW() - INTERVAL '30 days';
    """))
    row = result.first()
    print(f"\nDashboard Query Result:")
    print(f"  Delivered: {row.delivered}")
    print(f"  Pending: {row.pending}")
    print(f"  Total: {row.total}")
