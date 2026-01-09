from sqlalchemy import create_engine, text
from app.database import engine

with engine.connect() as conn:
    # Total Revenue from orders table
    result = conn.execute(text("""
        SELECT 
            COALESCE(SUM(amount), 0)::float as total_revenue,
            COUNT(*)::int as total_orders
        FROM orders
        WHERE created_at >= NOW() - INTERVAL '100 years';
    """))
    row = result.first()
    total_revenue = row.total_revenue if row.total_revenue else 0
    total_orders = row.total_orders if row.total_orders else 0
    
    print(f"📊 TOTAL REVENUE (from orders.amount):")
    print(f"   Revenue: ₹{total_revenue:,.2f}")
    print(f"   Orders: {total_orders}")
    
    # Revenue from Best Sellers (JSONB products)
    result = conn.execute(text("""
        SELECT 
            p->>'name' as name,
            SUM((p->>'quantity')::int) as sales,
            SUM((p->>'price')::float * (p->>'quantity')::int)::float as revenue
        FROM orders, jsonb_array_elements(products::jsonb) AS p
        WHERE created_at >= NOW() - INTERVAL '100 years'
        GROUP BY p->>'name'
        ORDER BY revenue DESC;
    """))
    
    print(f"\n📦 BEST SELLERS (from orders.products JSONB):")
    total_best_sellers_revenue = 0
    for i, row in enumerate(result, 1):
        rev = row.revenue if row.revenue else 0
        print(f"   {i}. {row.name}: ₹{rev:,.2f} ({row.sales} units)")
        total_best_sellers_revenue += rev
    
    print(f"\n💰 COMPARISON:")
    print(f"   Total Revenue (orders.amount): ₹{total_revenue:,.2f}")
    print(f"   Best Sellers Sum (products JSONB): ₹{total_best_sellers_revenue:,.2f}")
    print(f"   Difference: ₹{abs(total_revenue - total_best_sellers_revenue):,.2f}")
    
    # Check if there are orders with NULL or empty products
    result = conn.execute(text("""
        SELECT COUNT(*) as count
        FROM orders
        WHERE products IS NULL OR products::text = '[]' OR products::text = 'null';
    """))
    null_count = result.scalar()
    print(f"\n⚠️  Orders with NULL/empty products: {null_count}")

