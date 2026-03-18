from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class DashboardService:
    @staticmethod
    def get_overview_data(db: Session, timeframe: str):
        # 1. Map timeframes to SQL intervals
        intervals = {
            "today": "1 day",
            "weekly": "7 days",
            "monthly": "30 days",
            "all": "100 years"
        }
        interval = intervals.get(timeframe.lower(), "30 days")

        # 2. Main KPI Metrics
        kpi_query = text(f"""
            SELECT 
                (SELECT COALESCE(SUM(amount), 0)::float FROM public.transactions WHERE status = 'SUCCESS' AND created_at >= NOW() - INTERVAL '{interval}') as revenue,
                COUNT(*)::int as orders,
                (
                    (SELECT COUNT(*)::int FROM public.users WHERE created_at >= NOW() - INTERVAL '{interval}') +
                    (SELECT COUNT(*)::int FROM public.b2c_applications WHERE created_at >= NOW() - INTERVAL '{interval}') +
                    (SELECT COUNT(*)::int FROM public.b2b_applications WHERE created_at >= NOW() - INTERVAL '{interval}')
                ) as users,
                (SELECT COUNT(*)::int FROM public.exchanges WHERE created_at >= NOW() - INTERVAL '{interval}') as refunds
            FROM public.orders
            WHERE created_at >= NOW() - INTERVAL '{interval}';
        """)
        
        # 3. B2B vs B2C Analytics Chart
        chart_query = text(f"""
            SELECT 
                TO_CHAR(created_at, 'Mon DD') as name,
                SUM(CASE WHEN customer_type = 'B2B' THEN amount ELSE 0 END)::float as b2b,
                SUM(CASE WHEN customer_type = 'B2C' THEN amount ELSE 0 END)::float as b2c
            FROM public.orders
            WHERE created_at >= NOW() - INTERVAL '{interval}'
            GROUP BY name, DATE_TRUNC('day', created_at)
            ORDER BY DATE_TRUNC('day', created_at);
        """)

        # 4. Best Selling Products (Including Tax - proportional to order amount)
        # Handles both 'quantity' and 'qty' field names
        sellers_query = text(f"""
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
            ORDER BY revenue DESC LIMIT 5;
        """)

        # 5. Real Delivery Stats from deliveries table (case-insensitive)
        delivery_query = text(f"""
            SELECT 
                COUNT(CASE WHEN UPPER(delivery_status) IN ('DELIVERED', 'COMPLETED') THEN 1 END)::int as delivered,
                COUNT(CASE WHEN UPPER(delivery_status) IN ('PENDING', 'IN TRANSIT', 'READY TO PICKUP', 'AWB GENERATED', 'PICKUP SCHEDULED', 'PICKUP_SCHEDULED', 'PICKED UP', 'PICKED_UP', 'OUT FOR DELIVERY', 'OUT_FOR_DELIVERY', 'RTO') THEN 1 END)::int as pending,
                COUNT(*)::int as total
            FROM public.deliveries
            WHERE created_at >= NOW() - INTERVAL '{interval}';
        """)
        
        try:
            kpis = db.execute(kpi_query).mappings().first()
            chart = db.execute(chart_query).mappings().all()
            sellers = db.execute(sellers_query).mappings().all()
            delivery_stats = db.execute(delivery_query).mappings().first()
            
            # Calculate delivery percentages (On Time = Delivered, Late = Pending/In Transit)
            total_deliveries = delivery_stats['total']
            if total_deliveries > 0:
                delivered_count = delivery_stats['delivered']
                pending_count = delivery_stats['pending']
                
                # Build porter_data, only include categories with values > 0
                porter_data = []
                if delivered_count > 0:
                    porter_data.append({"name": "Delivered", "value": delivered_count, "color": "#10B981"})
                if pending_count > 0:
                    porter_data.append({"name": "Pending", "value": pending_count, "color": "#EF4444"})
                
                # If somehow both are 0 (shouldn't happen if total > 0), use fallback
                if not porter_data:
                    porter_data = [
                        {"name": "No Data", "value": 1, "color": "#9CA3AF"}
                    ]
            else:
                # Fallback to default if no delivery data
                porter_data = [
                    {"name": "No Deliveries", "value": 1, "color": "#9CA3AF"}
                ]

            return {
                "revenue": {"value": f"₹{kpis['revenue']:,}", "percent": "+12%", "trend": "up", "subtext": "vs last period"},
                "orders": {"value": str(kpis['orders']), "percent": "+5%", "trend": "up", "subtext": "vs last period"},
                "users": {"value": str(kpis['users']), "percent": "+8%", "trend": "up", "subtext": "new signups"},
                "refunds": {"value": str(kpis['refunds']), "percent": "-2%", "trend": "down", "subtext": "vs last period"},
                "chart": chart,
                "bestSellers": sellers,
                "porter": porter_data
            }
        except Exception as e:
            logger.error(f"Dashboard Service Error: {e}")
            return None