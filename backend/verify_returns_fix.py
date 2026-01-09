from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    # Test the combined returns query
    result = conn.execute(text("""
        SELECT reason as name, COUNT(*)::int as value 
        FROM (
            SELECT reason FROM public.exchanges
            UNION ALL
            SELECT reason FROM public.refunds
        ) AS combined_returns
        GROUP BY reason
        ORDER BY value DESC;
    """))
    
    print("📊 REPORTS - RETURNS (Exchanges + Refunds):\n")
    total = 0
    for i, row in enumerate(result, 1):
        print(f"{i}. {row.name}: {row.value} cases")
        total += row.value
    
    print(f"\n💰 Total Return Cases: {total}")
    
    # Show breakdown
    result = conn.execute(text("SELECT COUNT(*) as count FROM exchanges"))
    exchanges_count = result.scalar()
    
    result = conn.execute(text("SELECT COUNT(*) as count FROM refunds"))
    refunds_count = result.scalar()
    
    print(f"\n📦 Breakdown:")
    print(f"   Exchanges: {exchanges_count}")
    print(f"   Refunds: {refunds_count}")
    print(f"   Total: {exchanges_count + refunds_count}")
