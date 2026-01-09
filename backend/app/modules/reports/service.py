from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class ReportsService:
    @staticmethod
    def get_sales_report(db: Session, timeframe: str):
        time_mapping = {"daily": "1 day", "weekly": "7 days", "monthly": "30 days", "yearly": "1 year", "all": "100 years"}
        interval = time_mapping.get(timeframe.lower(), "30 days")
        date_trunc = 'hour' if timeframe.lower() == 'daily' else 'day'
        
        # 1. Stats Query
        stats_query = text(f"""
            SELECT COALESCE(SUM(amount), 0)::float as total_sales, COUNT(*)::int as total_orders,
            CASE WHEN COUNT(*) > 0 THEN COALESCE(SUM(amount), 0)::float / COUNT(*) ELSE 0 END as avg_order_value
            FROM public.orders WHERE created_at >= NOW() - INTERVAL '{interval}';
        """)

        # 2. Chart Query
        chart_query = text(f"""
            SELECT TO_CHAR(DATE_TRUNC('{date_trunc}', created_at), 'YYYY-MM-DD HH24:MI') as name,
            COALESCE(SUM(amount), 0)::float as sales, COUNT(*)::int as orders
            FROM public.orders WHERE created_at >= NOW() - INTERVAL '{interval}'
            GROUP BY DATE_TRUNC('{date_trunc}', created_at) ORDER BY DATE_TRUNC('{date_trunc}', created_at);
        """)

        # 3. Top Products Query (Including Tax - proportional to order amount)
        products_query = text(f"""
            WITH product_revenue AS (
                SELECT 
                    p->>'name' as product_name,
                    COALESCE((p->>'quantity')::int, (p->>'qty')::int, 0) as quantity,
                    ((p->>'price')::float * COALESCE((p->>'quantity')::int, (p->>'qty')::int, 0)) as product_subtotal,
                    o.amount as order_total,
                    o.id as order_id
                FROM public.orders o, jsonb_array_elements(o.products) AS p
                WHERE o.created_at >= NOW() - INTERVAL '{interval}'
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
        """)

        try:
            stats = db.execute(stats_query).mappings().first()
            chart = db.execute(chart_query).mappings().all()
            products = db.execute(products_query).mappings().all()
            return {
                "stats": {"total_sales": stats['total_sales'], "total_orders": stats['total_orders'], "avg_order_value": stats['avg_order_value']},
                "chart": chart if chart else [],
                "top_products": products if products else []
            }
        except Exception as e:
            logger.error(f"Sales Report Error: {e}")
            return {"stats": {"total_sales": 0, "total_orders": 0, "avg_order_value": 0}, "chart": [], "top_products": []}

    @staticmethod
    def get_delivery_stats(db: Session):
        query = text("SELECT delivery_status as name, COUNT(*)::int as value FROM public.deliveries GROUP BY delivery_status;")
        return db.execute(query).mappings().all()

    @staticmethod
    def get_segment_analysis(db: Session):
        query = text("SELECT customer_type as name, COUNT(*)::int as value FROM public.orders GROUP BY customer_type;")
        return db.execute(query).mappings().all()

    @staticmethod
    def get_return_analysis(db: Session):
        # Combine data from both exchanges and refunds tables
        query = text("""
            SELECT reason as name, COUNT(*)::int as value 
            FROM (
                SELECT reason FROM public.exchanges
                UNION ALL
                SELECT reason FROM public.refunds
            ) AS combined_returns
            GROUP BY reason
            ORDER BY value DESC;
        """)
        return db.execute(query).mappings().all()