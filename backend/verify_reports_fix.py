from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    # Test the new Reports top products query with tax included
    result = conn.execute(text("""
        WITH product_revenue AS (
            SELECT 
                p->>'name' as product_name,
                COALESCE((p->>'quantity')::int, (p->>'qty')::int, 0) as quantity,
                ((p->>'price')::float * COALESCE((p->>'quantity')::int, (p->>'qty')::int, 0)) as product_subtotal,
                o.amount as order_total,
                o.id as order_id
            FROM public.orders o, jsonb_array_elements(o.products) AS p
            WHERE o.created_at >= NOW() - INTERVAL '100 years'
        ),
        order_subtotals AS (
            SELECT 
                order_id,
                SUM(product_subtotal) as order_subtotal
            FROM product_revenue
            GROUP BY order_id
        )
        SELECT 
            COALESCE(pr.product_name, 'Unknown Product') as name,
            SUM(pr.quantity)::int as sales,
            SUM(
                CASE 
                    WHEN ost.order_subtotal > 0 THEN 
                        (pr.product_subtotal / ost.order_subtotal) * pr.order_total
                    ELSE 0 
                END
            )::float as revenue
        FROM product_revenue pr
        JOIN order_subtotals ost ON pr.order_id = ost.order_id
        GROUP BY pr.product_name
        ORDER BY revenue DESC LIMIT 10;
    """))
    
    print("📊 REPORTS - TOP PRODUCTS (Including Tax):\n")
    total_revenue = 0
    for i, row in enumerate(result, 1):
        print(f"{i}. {row.name}")
        print(f"   Sales: {row.sales} units")
        print(f"   Revenue: ₹{row.revenue:,.2f}")
        total_revenue += row.revenue
    
    print(f"\n💰 Total Product Revenue (with tax): ₹{total_revenue:,.2f}")
    
    # Compare with total order amount
    result = conn.execute(text("SELECT SUM(amount) as total FROM orders"))
    order_total = float(result.scalar() or 0)
    print(f"💰 Total Order Amount: ₹{order_total:,.2f}")
    print(f"\n✅ Match: {abs(total_revenue - order_total) < 0.01}")
