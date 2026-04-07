from sqlalchemy.orm import Session, joinedload
from app.modules.orders.models import Order, Delivery
from app.modules.exchanges.models import Exchange
from typing import List
import logging
import json

from app.modules.delivery.shipment_service import create_shipment_for_order

logger = logging.getLogger(__name__)


def get_all_orders(db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
    return (
        db.query(Order)
        # .options(
        #     joinedload(Order.b2b_application),
        #     joinedload(Order.b2c_application)
        # )
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_order_by_id(db: Session, order_id: str):
    return (
        db.query(Order)
        # .options(
        #     joinedload(Order.b2b_application),
        #     joinedload(Order.b2c_application)
        # )
        .filter(Order.order_id == order_id)
        .first()
    )


def update_order_status(db: Session, order_id: str, status: str):
    logger.info(f"[ORDER] Update requested: {order_id} → {status}")

    order = (
        db.query(Order)
        # .options(
        #     joinedload(Order.b2b_application),
        #     joinedload(Order.b2c_application)
        # )
        .filter(Order.order_id == order_id)
        .first()
    )

    if not order:
        logger.error("[ORDER] Order not found")
        return None

    try:
        order.status = status
        db.commit()
        db.refresh(order)

        print(f"[DEBUG] Order {order_id} status updated to: {status}")
        logger.info("[ORDER] Status updated successfully")

        print(f"==================================================")
        print(f"[DEBUG] Order {order_id} status update requested: '{status}'")
        
        # Case-insensitive check
        if status.lower() == "ready to pickup":
            print(f"[DEBUG] Condition MATCHED: '{status}' == 'Ready to Pickup'")
            print("[DEBUG] Step 1: Creating Delivery Entry...")
            create_delivery_entry(db, order)

            print("[DEBUG] Step 2: Triggering Shipment Creation (Delhivery)...")
            awb = create_shipment_for_order(db, order)
            
            if awb:
                print(f"**************************************************")
                print(f"SUCCESS: AWB Generated: {awb}")
                print(f"**************************************************")
            else:
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print(f"FAILURE: AWB Generation Failed. Check logs.")
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        else:
            print(f"[DEBUG] Condition FAILED: '{status}' != 'Ready to Pickup'")
            print(f"[DEBUG] Skipping Delivery/Shipment flow.")
        
        print(f"==================================================")

        return order

    except Exception:
        logger.exception("[ERROR] Failed during Ready to Pickup flow")
        db.rollback()
        raise


def create_delivery_entry(db: Session, order: Order):
    """
    DB ONLY — NO DELHIVERY API CALLS HERE
    """

    customer_name = order.customer_name or "Customer"

    existing = db.query(Delivery).filter(
        Delivery.order_id == order.id
    ).first()

    if existing:
        logger.info(f"[DELIVERY] Delivery already exists for {order.order_id}")
        return existing

    # Process Products
    item_names = []
    total_qty = 0
    
    products_data = order.products
    
    # Handle string JSON if needed
    if isinstance(products_data, str):
        try:
            # Fix common python string representation issues if any
            fixed_json = products_data.replace("'", '"').replace("None", "null").replace("False", "false").replace("True", "true")
            products_data = json.loads(fixed_json)
        except:
            products_data = []
            
    # Handle single object
    if isinstance(products_data, dict):
        products_data = [products_data]
        
    if products_data and isinstance(products_data, list):
        for item in products_data:
            if isinstance(item, dict):
                name = item.get('name') or item.get('product_name') or item.get('product') or 'Item'
                try:
                    qty = int(item.get('quantity') or item.get('qty') or 1)
                except:
                    qty = 1
                item_names.append(f"{name} x{qty}")
                total_qty += qty
            
    item_name_str = ", ".join(item_names)
    if len(item_name_str) > 255:
        item_name_str = item_name_str[:252] + "..."

    delivery = Delivery(
        order_id=order.id,
        weight=order.weight or 0,
        length=order.length or 0,
        breadth=order.breadth or 0,
        height=order.height or 0,
        pickup_location="sevenxt",
        payment=order.payment or "Unpaid",
        amount=order.amount or 0,
        customer_name=customer_name,
        phone=order.phone or "",
        full_address=order.address or "",
        city=order.city if hasattr(order, 'city') else None,
        state=order.state if hasattr(order, 'state') else None,
        pincode=order.pincode if hasattr(order, 'pincode') else None,
        delivery_status="Ready to Pickup",
        item_name=item_name_str,
        quantity=total_qty
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    logger.info(f"[DELIVERY] Delivery entry created for {order.order_id}")
    return delivery


def get_all_deliveries(db: Session, skip: int = 0, limit: int = 100) -> List[Delivery]:
    return (
        db.query(Delivery)
        .options(joinedload(Delivery.order))
        .order_by(Delivery.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_delivery_schedule(db: Session, delivery_id: int, schedule_pickup):
    # Check for Exchange IDs (Virtual IDs)
    if delivery_id > 50000:
        return update_exchange_delivery_schedule(db, delivery_id, schedule_pickup)

    delivery = db.query(Delivery).options(joinedload(Delivery.order)).filter(Delivery.id == delivery_id).first()
    if delivery:
        delivery.schedule_pickup = schedule_pickup
        delivery.delivery_status = "Pickup Time Scheduled"
        
        # Update associated Order status
        if delivery.order:
            delivery.order.status = "Pickup Time Scheduled"
            
        db.commit()
        db.refresh(delivery)

        # --- Trigger Delhivery Pickup Request ---
        try:
            from app.modules.delivery.delhivery_client import delhivery_client
            
            # Format date and time
            # schedule_pickup is a datetime object
            pickup_date = schedule_pickup.strftime("%Y-%m-%d")
            pickup_time = schedule_pickup.strftime("%H:%M:%S")
            
            print(f"[PICKUP] Scheduling pickup for Delivery {delivery.id} at {pickup_date} {pickup_time}")
            
            response = delhivery_client.pickup_request({
                "pickup_time": pickup_time,
                "pickup_date": pickup_date,
                "pickup_location": delivery.pickup_location,
                "expected_package_count": delivery.quantity
            })
            
            print(f"[PICKUP] Successfully scheduled: {response}")
            
        except Exception as e:
            print(f"[PICKUP] Failed to schedule with Delhivery: {e}")
            # We don't rollback DB here because the local schedule is still valid intent
            # Ideally, we should store the error or retry status
            
    return delivery


def update_exchange_delivery_schedule(db: Session, delivery_id: int, schedule_pickup):
    """
    Handle pickup scheduling for Exchange orders (Virtual IDs)
    """
    is_new_shipment = False
    exchange_id = 0
    
    if delivery_id > 60000:
        is_new_shipment = True
        exchange_id = delivery_id - 60000
    else:
        exchange_id = delivery_id - 50000
        
    exchange = db.query(Exchange).options(joinedload(Exchange.order)).filter(Exchange.id == exchange_id).first()
    if not exchange:
        return None
        
    # Trigger Delhivery Pickup
    try:
        from app.modules.delivery.delhivery_client import delhivery_client
        
        pickup_date = schedule_pickup.strftime("%Y-%m-%d")
        pickup_time = schedule_pickup.strftime("%H:%M:%S")
        
        # Determine location
        # For New Shipment (Warehouse -> Customer), pickup is from Warehouse ("sevenxt")
        # For Return Shipment (Customer -> Warehouse), pickup is technically from Customer
        # BUT Delhivery API often requires a registered warehouse name for pickup_location.
        # If we use "sevenxt", the courier comes to warehouse.
        # For Returns, usually the pickup is scheduled during creation or via a different flow.
        # However, to support the button action, we'll use "sevenxt" as default if that's what works for the client,
        # OR we might need to skip the API call if it's a return and just update status?
        # Let's try to schedule it.
        location = "sevenxt" 
             
        print(f"[PICKUP] Scheduling pickup for Exchange {exchange_id} ({'New' if is_new_shipment else 'Return'}) at {pickup_date} {pickup_time}")
        
        response = delhivery_client.pickup_request({
            "pickup_time": pickup_time,
            "pickup_date": pickup_date,
            "pickup_location": location,
            "expected_package_count": exchange.quantity
        })
        
        print(f"[PICKUP] Successfully scheduled: {response}")
        
    except Exception as e:
        print(f"[PICKUP] Failed to schedule with Delhivery: {e}")

    # Update Status
    status_msg = "Pickup Time Scheduled"
    if is_new_shipment:
        exchange.new_delivery_status = status_msg
        # Sync with Parent Order Status
        if exchange.order:
            exchange.order.status = status_msg
    else:
        exchange.return_delivery_status = status_msg
        
    db.commit()
    db.refresh(exchange)
    
    # Construct Virtual Delivery Object
    class VirtualDelivery:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            
    return VirtualDelivery(
        id=delivery_id,
        order_id=exchange.order.id if exchange.order else 0,
        order=exchange.order,
        weight=0, length=0, breadth=0, height=0,
        awb_number=exchange.new_awb_number if is_new_shipment else exchange.return_awb_number,
        courier_partner="Delhivery",
        pickup_location="Warehouse" if is_new_shipment else "Customer Return",
        payment="Prepaid",
        amount=0,
        customer_name=exchange.customer_name,
        phone=exchange.order.phone if exchange.order else "",
        full_address=exchange.order.address if exchange.order else "",
        city=exchange.order.city if exchange.order else "",
        state=exchange.order.state if exchange.order else "",
        pincode=exchange.order.pincode if exchange.order else "",
        item_name=f"{'Exchange' if is_new_shipment else 'Return'}: {exchange.product_name}",
        quantity=exchange.quantity,
        schedule_pickup=schedule_pickup,
        delivery_status=status_msg,
        awb_label_path=exchange.new_label_path if is_new_shipment else exchange.return_label_path,
        created_at=exchange.created_at,
        updated_at=exchange.updated_at
    )


def update_order_dimensions(
    db: Session,
    order_id: str,
    height: float,
    weight: float,
    breadth: float,
    length: float,
):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if order:
        order.height = height
        order.weight = weight
        order.breadth = breadth
        order.length = length
        db.commit()
        db.refresh(order)
    return order


def update_order_awb(db: Session, order_id: str, new_awb_number: str, new_label_path: str = None):
    """
    Update order AWB number and label (used for exchanges)
    Replaces old AWB with new AWB
    """
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if order:
        order.awb_number = new_awb_number
        # Note: Order model doesn't have awb_label_path, it's in Delivery table
        # Update delivery table as well
        delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
        if delivery:
            delivery.awb_number = new_awb_number
            if new_label_path:
                delivery.awb_label_path = new_label_path
        
        db.commit()
        db.refresh(order)
        logger.info(f"Updated AWB for order {order_id} to {new_awb_number}")
    return order
