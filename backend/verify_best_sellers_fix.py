from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    # Test the new Best Sellers query with COALESCE for quantity/qty
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
            pr.product_name as name,
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
        ORDER BY revenue DESC;
    """))
    
    print("📦 BEST SELLERS (NEW - Including Tax):")
    total = 0
    for i, row in enumerate(result, 1):
        rev = row.revenue if row.revenue else 0
        print(f"   {i}. {row.name}: ₹{rev:,.2f} ({row.sales} units)")
        total += rev
    
    print(f"\n💰 Total Best Sellers Revenue: ₹{total:,.2f}")
    
    # Compare with Total Revenue
    result = conn.execute(text("""
        SELECT COALESCE(SUM(amount), 0)::float as total_revenue
        FROM orders
        WHERE created_at >= NOW() - INTERVAL '100 years';
    """))
    total_revenue = result.scalar()
    
    print(f"💰 Total Revenue (orders.amount): ₹{total_revenue:,.2f}")
    print(f"\n✅ Match: {abs(total - total_revenue) < 0.01}")

