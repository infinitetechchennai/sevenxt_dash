<<<<<<< HEAD
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/recent")
def get_recent_notifications(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get recent notifications for orders, refunds, and exchanges"""
    try:
        notifications = []
        
        # Recent Orders (last 24 hours)
        orders_query = text("""
            SELECT 
                'order' as type,
                order_id as reference_id,
                customer_name,
                amount::float,
                status,
                created_at
            FROM public.orders
            WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 10;
        """)
        
        # Recent Refunds (last 24 hours)
        refunds_query = text("""
            SELECT 
                'refund' as type,
                r.order_id::text as reference_id,
                o.customer_name,
                r.amount::float,
                r.status,
                r.created_at
            FROM public.refunds r
            LEFT JOIN public.orders o ON r.order_id = o.id
            WHERE r.created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            ORDER BY r.created_at DESC
            LIMIT 10;
        """)
        
        # Recent Exchanges (last 24 hours)
        exchanges_query = text("""
            SELECT 
                'exchange' as type,
                order_id as reference_id,
                product_name,
                reason,
                status,
                created_at
            FROM public.exchanges
            WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 10;
        """)
        
        # Execute queries
        orders = db.execute(orders_query).mappings().all()
        refunds = db.execute(refunds_query).mappings().all()
        exchanges = db.execute(exchanges_query).mappings().all()
        
        # Format notifications
        for order in orders:
            notifications.append({
                "id": f"order-{order['reference_id']}",
                "type": "order",
                "title": "New Order Received",
                "message": f"Order {order['reference_id']} from {order['customer_name']} - ₹{order['amount']:.2f}",
                "status": order['status'],
                "timestamp": order['created_at'].isoformat() if order['created_at'] else None,
                "reference_id": order['reference_id']
            })
        
        for refund in refunds:
            notifications.append({
                "id": f"refund-{refund['reference_id']}",
                "type": "refund",
                "title": "Refund Request",
                "message": f"Refund for order {refund['reference_id']} - {refund['customer_name']} - ₹{refund['amount']:.2f}",
                "status": refund['status'],
                "timestamp": refund['created_at'].isoformat() if refund['created_at'] else None,
                "reference_id": refund['reference_id']
            })
        
        for exchange in exchanges:
            notifications.append({
                "id": f"exchange-{exchange['reference_id']}",
                "type": "exchange",
                "title": "Exchange Request",
                "message": f"Exchange for {exchange['product_name']} - Reason: {exchange['reason']}",
                "status": exchange['status'],
                "timestamp": exchange['created_at'].isoformat() if exchange['created_at'] else None,
                "reference_id": exchange['reference_id']
            })
        
        # Sort all notifications by timestamp
        notifications.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '', reverse=True)
        
        return notifications[:20]  # Return top 20 most recent
        
    except Exception as e:
        logger.error(f"Notifications Error: {e}")
        logger.exception("Full traceback:")
        return []

@router.get("/count")
def get_notification_count(db: Session = Depends(get_db)) -> Dict[str, int]:
    """Get count of unread notifications"""
    try:
        count_query = text("""
            SELECT 
                (SELECT COUNT(*) FROM public.orders WHERE created_at >= NOW() - INTERVAL '24 hours')::int as orders,
                (SELECT COUNT(*) FROM public.refunds WHERE created_at >= NOW() - INTERVAL '24 hours')::int as refunds,
                (SELECT COUNT(*) FROM public.exchanges WHERE created_at >= NOW() - INTERVAL '24 hours')::int as exchanges;
        """)
        
        result = db.execute(count_query).mappings().first()
        
        total = (result['orders'] or 0) + (result['refunds'] or 0) + (result['exchanges'] or 0)
        
        return {
            "total": total,
            "orders": result['orders'] or 0,
            "refunds": result['refunds'] or 0,
            "exchanges": result['exchanges'] or 0
        }
    except Exception as e:
        logger.error(f"Notification Count Error: {e}")
        return {"total": 0, "orders": 0, "refunds": 0, "exchanges": 0}

@router.get("/debug")
def debug_notifications(db: Session = Depends(get_db)):
    """Debug endpoint to check orders table"""
    try:
        # Check total orders
        total_query = text("SELECT COUNT(*) as total FROM public.orders;")
        total_result = db.execute(total_query).mappings().first()
        
        # Check recent orders
        recent_query = text("""
            SELECT order_id, customer_name, created_at, 
                   CURRENT_TIMESTAMP as now,
                   CURRENT_TIMESTAMP - INTERVAL '24 hours' as cutoff
            FROM public.orders 
            ORDER BY created_at DESC 
            LIMIT 5;
        """)
        recent_orders = db.execute(recent_query).mappings().all()
        
        return {
            "total_orders": total_result['total'],
            "recent_orders": [dict(r) for r in recent_orders],
            "current_time": str(db.execute(text("SELECT CURRENT_TIMESTAMP;")).scalar())
        }
    except Exception as e:
        logger.exception("Debug error:")
        return {"error": str(e)}
=======
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.modules.orders.models import Order
from app.modules.refunds.models import Refund
from app.modules.exchanges.models import Exchange
from datetime import datetime, timedelta
from typing import List, Dict, Any

router = APIRouter()

@router.get("/today")
def get_today_notifications(db: Session = Depends(get_db)):
    """
    Get all notifications for today (new orders, refunds, exchanges)
    """
    try:
        # Get today's date range
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        notifications = []
        
        # Fetch today's orders
        orders = db.query(Order).filter(
            Order.created_at >= today_start,
            Order.created_at <= today_end
        ).order_by(Order.created_at.desc()).all()
        
        for order in orders:
            notifications.append({
                "id": f"order_{order.id}",
                "type": "order",
                "title": "New Order Placed",
                "description": f"Order {order.order_id} placed by {order.customer_name or 'Customer'}",
                "timestamp": order.created_at.isoformat(),
                "status": "unread",
                "reference_id": order.order_id,
                "amount": float(order.amount) if order.amount else 0
            })
        
        # Fetch today's refunds
        refunds = db.query(Refund).filter(
            Refund.created_at >= today_start,
            Refund.created_at <= today_end
        ).order_by(Refund.created_at.desc()).all()
        
        for refund in refunds:
            order = db.query(Order).filter(Order.id == refund.order_id).first()
            notifications.append({
                "id": f"refund_{refund.id}",
                "type": "refund",
                "title": "Refund Requested",
                "description": f"Refund request for Order {order.order_id if order else 'N/A'} - ₹{float(refund.amount)}",
                "timestamp": refund.created_at.isoformat(),
                "status": "unread",
                "reference_id": order.order_id if order else None,
                "amount": float(refund.amount) if refund.amount else 0
            })
        
        # Fetch today's exchanges
        exchanges = db.query(Exchange).filter(
            Exchange.created_at >= today_start,
            Exchange.created_at <= today_end
        ).order_by(Exchange.created_at.desc()).all()
        
        for exchange in exchanges:
            notifications.append({
                "id": f"exchange_{exchange.id}",
                "type": "exchange",
                "title": "Exchange Requested",
                "description": f"Exchange request for Order {exchange.order_id} - {exchange.product_name}",
                "timestamp": exchange.created_at.isoformat(),
                "status": "unread",
                "reference_id": exchange.order_id,
                "reason": exchange.reason
            })
        
        # Sort all notifications by timestamp (newest first)
        notifications.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "success": True,
            "notifications": notifications,
            "count": len(notifications)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch notifications: {str(e)}")


@router.get("/recent")
def get_recent_notifications(limit: int = 50, db: Session = Depends(get_db)):
    """
    Get recent notifications (last 50 by default)
    """
    try:
        notifications = []
        
        # Fetch recent orders
        orders = db.query(Order).order_by(Order.created_at.desc()).limit(limit).all()
        
        for order in orders:
            notifications.append({
                "id": f"order_{order.id}",
                "type": "order",
                "title": "New Order Placed",
                "description": f"Order {order.order_id} placed by {order.customer_name or 'Customer'}",
                "timestamp": order.created_at.isoformat(),
                "status": "read",
                "reference_id": order.order_id,
                "amount": float(order.amount) if order.amount else 0
            })
        
        # Fetch recent refunds
        refunds = db.query(Refund).order_by(Refund.created_at.desc()).limit(limit).all()
        
        for refund in refunds:
            order = db.query(Order).filter(Order.id == refund.order_id).first()
            notifications.append({
                "id": f"refund_{refund.id}",
                "type": "refund",
                "title": "Refund Requested",
                "description": f"Refund request for Order {order.order_id if order else 'N/A'} - ₹{float(refund.amount)}",
                "timestamp": refund.created_at.isoformat(),
                "status": "read",
                "reference_id": order.order_id if order else None,
                "amount": float(refund.amount) if refund.amount else 0
            })
        
        # Fetch recent exchanges
        exchanges = db.query(Exchange).order_by(Exchange.created_at.desc()).limit(limit).all()
        
        for exchange in exchanges:
            notifications.append({
                "id": f"exchange_{exchange.id}",
                "type": "exchange",
                "title": "Exchange Requested",
                "description": f"Exchange request for Order {exchange.order_id} - {exchange.product_name}",
                "timestamp": exchange.created_at.isoformat(),
                "status": "read",
                "reference_id": exchange.order_id,
                "reason": exchange.reason
            })
        
        # Sort all notifications by timestamp (newest first)
        notifications.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limit to the requested number
        notifications = notifications[:limit]
        
        return {
            "success": True,
            "notifications": notifications,
            "count": len(notifications)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch notifications: {str(e)}")
>>>>>>> 18b14a9a377cc9a7ca746e390bd3e86ba8561ad7
