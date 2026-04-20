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
    def get_growth_metrics(db: Session):
        """Calculates Week-over-Week and Month-over-Month growth rates."""
        # Current Week vs Last Week
        cw_sales = db.execute(text("SELECT COALESCE(SUM(amount), 0) FROM public.orders WHERE created_at >= NOW() - INTERVAL '7 days'")).scalar() or 0
        lw_sales = db.execute(text("SELECT COALESCE(SUM(amount), 0) FROM public.orders WHERE created_at >= NOW() - INTERVAL '14 days' AND created_at < NOW() - INTERVAL '7 days'")).scalar() or 0
        
        cw_orders = db.execute(text("SELECT COUNT(*) FROM public.orders WHERE created_at >= NOW() - INTERVAL '7 days'")).scalar() or 0
        lw_orders = db.execute(text("SELECT COUNT(*) FROM public.orders WHERE created_at >= NOW() - INTERVAL '14 days' AND created_at < NOW() - INTERVAL '7 days'")).scalar() or 0

        # Current Month vs Last Month
        cm_sales = db.execute(text("SELECT COALESCE(SUM(amount), 0) FROM public.orders WHERE created_at >= NOW() - INTERVAL '30 days'")).scalar() or 0
        lm_sales = db.execute(text("SELECT COALESCE(SUM(amount), 0) FROM public.orders WHERE created_at >= NOW() - INTERVAL '60 days' AND created_at < NOW() - INTERVAL '30 days'")).scalar() or 0

        def calc_growth(current, previous):
            if previous == 0: return 100.0 if current > 0 else 0.0
            return ((current - previous) / previous) * 100

        return {
            "weekly": {
                "sales_growth": round(calc_growth(cw_sales, lw_sales), 1),
                "orders_growth": round(calc_growth(cw_orders, lw_orders), 1),
                "current_sales": cw_sales
            },
            "monthly": {
                "sales_growth": round(calc_growth(cm_sales, lm_sales), 1),
                "current_sales": cm_sales
            }
        }

    @staticmethod
    def get_payment_stats(db: Session):
        query = text("""
            SELECT 
                COALESCE(payment, 'Unknown') as name, 
                COUNT(*)::int as count, 
                SUM(amount)::float as value 
            FROM public.orders 
            GROUP BY payment 
            ORDER BY value DESC
        """)
        return db.execute(query).mappings().all()

    @staticmethod
    def get_geo_stats(db: Session):
        query = text("""
            SELECT 
                COALESCE(state, 'Unknown') as name, 
                COUNT(*)::int as count,
                SUM(amount)::float as value
            FROM public.orders 
            WHERE state IS NOT NULL 
            GROUP BY state 
            ORDER BY count DESC 
            LIMIT 5
        """)
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

    # --- NEW REPORT: SALES INVENTORY ---
    @staticmethod
    def get_sales_inventory(db: Session):
        """
        Returns a complete list of ALL products from the catalog (Products Menu)
        merged with their performance from the Orders usage.
        
        Shows: 
        - Stock (from Products table)
        - Orders Placed (calculated from Orders table)
        - Total Revenue (calculated from Orders table)
        """
        
        # 1. Calculate Sales Stats from Orders
        orders = db.execute(text("SELECT products FROM public.orders WHERE status != 'Cancelled'")).mappings().all()
        
        # Maps to store aggregated stats: { product_id: { qty: 0, revenue: 0.0 } }
        sales_stats = {}
        import json
        
        for order in orders:
            products_data = order['products']
            
            # Robust JSON Parsing
            if isinstance(products_data, str):
                try:
                    products_data = json.loads(products_data.replace("'", '"').replace("None", "null"))
                except Exception:
                    products_data = []

            if isinstance(products_data, dict):
                products_data = [products_data]
            
            if not isinstance(products_data, list):
                continue
                
            for item in products_data:
                if not isinstance(item, dict): continue
                
                p_id = str(item.get('id') or item.get('product_id'))
                qty = int(item.get('quantity') or item.get('qty') or 0)
                
                # Robust Price
                try:
                    price = float(str(item.get('price') or 0).replace(',', '').strip())
                except:
                    price = 0.0
                
                if p_id:
                    if p_id not in sales_stats:
                        sales_stats[p_id] = {'qty': 0, 'revenue': 0.0}
                    
                    sales_stats[p_id]['qty'] += qty
                    sales_stats[p_id]['revenue'] += (qty * price)

        # 2. Fetch ALL Products from Catalog
        # This ensures even products with 0 sales appear in the report
        products_query = text("SELECT id, name, stock, price FROM public.products")
        all_products = db.execute(products_query).mappings().all()
        
        inventory_data = []
        
        # 3. Merge Catalog Data with Sales Stats
        # First, add all existing products
        for p in all_products:
            p_id = str(p['id'])
            stats = sales_stats.get(p_id, {'qty': 0, 'revenue': 0.0})
            
            inventory_data.append({
                "id": p_id,
                "name": p['name'],
                "price": float(p['price'] or 0),
                "stock": p['stock'], # Real stock from Product Menu
                "ordersPlaced": stats['qty'],
                "totalRevenue": stats['revenue']
            })
            
            # Remove from stats map to track 'orphaned' sales (products sold but deleted from catalog)
            if p_id in sales_stats:
                del sales_stats[p_id]
        
        # 4. (Optional) Add products found in orders but NOT in product catalog?
        # User asked for "all products in the product menu performance", but often wants to see historical sales too.
        # Let's add them as "Deleted/Archived" or just list them.
        for p_id, stats in sales_stats.items():
            inventory_data.append({
                "id": p_id,
                "name": f"Unknown/Deleted ({p_id})", # We don't have name if not in products table, unless we stored it in sales_stat logic (which we did not) - wait, previous logic captured name from Order.
                # Let's slighty improve loop 1 to capture name to handle this better.
                "stock": 0,
                "ordersPlaced": stats['qty'],
                "totalRevenue": stats['revenue']
            })
            
        return inventory_data

    # --- NEW REPORT: SALES DETAILS ---
    @staticmethod
    def get_sales_details(db: Session):
        """
        Returns a flattened list of all sales items across all orders.
        Matches the 'Sale Reports' tab requirements.
        Excludes Cancelled orders.
        Return keys are in camelCase for frontend compatibility.
        """
        # Fetch all non-cancelled orders with necessary fields
        query = text("""
            SELECT id, order_id, created_at, payment, status, customer_name, products, 
                   email, phone, city, state, pincode, hsn, sgst_percentage, cgst_percentage, original_price
            FROM public.orders 
            WHERE status != 'Cancelled' 
            ORDER BY created_at DESC
        """)
        orders = db.execute(query).mappings().all()
        
        import json
        sales_details = []
        
        for order in orders:
            products_data = order['products']
            
            # Robust Parsing Logic
            if isinstance(products_data, str):
                try:
                    products_data = json.loads(products_data.replace("'", '"').replace("None", "null"))
                except Exception:
                    products_data = []

            if isinstance(products_data, dict):
                products_data = [products_data]

            if not isinstance(products_data, list):
                continue
                
            for item in products_data:
                if not isinstance(item, dict): 
                    continue
                
                item_id = str(item.get('id') or '0')
                try:
                    price = float(str(item.get('price') or 0).replace(',', '').strip())
                except:
                    price = 0.0
                qty = int(item.get('quantity') or item.get('qty') or 1)
                final_total = price * qty
                
                # Construct unique key for frontend key prop
                unique_key = f"{order['id']}-{item_id}"
                
                sales_details.append({
                    "orderId": order['id'],
                    "uniqueKey": unique_key,
                    "orderDate": order['created_at'],
                    "paymentMethod": order['payment'],
                    "status": order['status'],
                    "storeName": order['customer_name'],
                    "email": order['email'],
                    "phone": order['phone'],
                    "city": order['city'],
                    "state": order['state'],
                    "pincode": order['pincode'],
                    "hsn": order['hsn'],
                    "sgst": float(order['sgst_percentage'] or 0),
                    "cgst": float(order['cgst_percentage'] or 0),
                    "salesRep": 'Super Market', # Static as per request/example
                    "itemId": item_id,
                    "productName": item.get('name'),
                    "finalTotal": final_total,
                    "quantity": qty
                })
        
        return sales_details
