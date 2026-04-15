from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.modules.orders import schemas, service
from app.modules.exchanges.models import Exchange
from sqlalchemy.orm import joinedload
import logging
from PyPDF2 import PdfWriter as PdfMerger
import os
from datetime import datetime
from pathlib import Path
from app.modules.activity_logs.service import log_activity
from app.modules.auth.routes import get_current_employee

# Configure logging
logger = logging.getLogger(__name__)

# Define base directory (absolute path to backend folder)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("", response_model=List[schemas.OrderResponse])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all orders with customer names"""
    import json
    
    orders = service.get_all_orders(db, skip=skip, limit=limit)
    
    # Process orders
    result = []
    for order in orders:
        # Parse products JSON if it's a string
        products_data = order.products
        
        if isinstance(products_data, str):
            try:
                products_data = json.loads(products_data.replace("'", '"').replace("None", "null"))
            except Exception as e:
                logger.error(f"Failed to parse products JSON for order {order.order_id}: {e}")
                products_data = []
        
        if isinstance(products_data, dict):
            products_data = [products_data]
        
        # Ensure products is a list (no enrichment, use data as-is from orders table)
        if not isinstance(products_data, list):
            products_data = []
        
        # Add HSN from order table to each product
        if order.hsn and products_data:
            for product in products_data:
                if isinstance(product, dict) and 'hsn' not in product:
                    product['hsn'] = order.hsn
                    product['hsn_code'] = order.hsn
                    product['hsnCode'] = order.hsn
        
        # Resolve missing email
        resolve_email = order.email
        if not resolve_email or 'example.com' in resolve_email:
            try:
                from app.modules.orders.models import B2CApplication
                if order.phone:
                    # Flexible phone search
                    clean_phone = order.phone.replace('+91', '').replace(' ', '').strip()[-10:]
                    b2c = db.query(B2CApplication).filter(
                        (B2CApplication.phone_number == clean_phone) |
                        (B2CApplication.phone_number == f"+91{clean_phone}") |
                        (B2CApplication.phone_number == order.phone)
                    ).first()
                    if b2c and b2c.email:
                        resolve_email = b2c.email
            except Exception:
                pass

        tax_meta = service.get_order_tax_meta(order)
        order_dict = {
            "id": order.id,
            "order_id": order.order_id,
            "order_number": order.order_id,
            "razorpay_order_id": getattr(order, "razorpay_order_id", None),
            "gst_type": tax_meta["gst_type"],
            "seller_gstin": tax_meta["seller_gstin"],
            "igst_percentage": tax_meta["igst_percentage"],
            "customer_type": order.customer_type,
            "customer_name": order.customer_name,
            "user_id": None,
            "products": products_data,  # Use products data with HSN added
            "amount": float(order.amount) if order.amount else None,
            "payment": order.payment,
            "status": order.status,
            "awb_number": order.awb_number,
            "address": order.address,
            "email": resolve_email,
            "phone": order.phone,
            "city": order.city,
            "state": order.state,
            "pincode": order.pincode,
            "height": order.height,
            "weight": order.weight,
            "breadth": order.breadth,
            "length": order.length,
            "sgst_percentage": float(order.sgst_percentage) if order.sgst_percentage is not None else 0.0,
            "cgst_percentage": float(order.cgst_percentage) if order.cgst_percentage is not None else 0.0,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
        }
        
        result.append(order_dict)
    
    return result

@router.get("/deliveries", response_model=List[schemas.DeliveryResponse])
def read_deliveries(
    skip: int = 0, 
    limit: int = 100, 
    city: str = None, 
    exclude_city: str = None, 
    delivery_status: str = None, 
    min_status: str = None,
    db: Session = Depends(get_db)
):
    """
    Get deliveries with optional filtering
    
    Query Parameters:
    - city: Filter by city (e.g., "Chennai" for local deliveries)
    - exclude_city: Exclude deliveries from a city (e.g., "Chennai" to get outstation)
    - delivery_status: Filter by specific delivery status (exact match)
    - min_status: Filter by minimum status progress (e.g., "PICKED_UP" includes "IN_TRANSIT", "DELIVERED", etc.)
    - skip: Number of records to skip (default 0)
    - limit: Number of records to return (default 100)
    """
    try:
        deliveries = service.get_all_deliveries(db, skip=skip, limit=limit)
        
        # --- Include Exchange Shipments ---
        # Fetch exchanges that have active shipments (Return or New)
        exchanges = db.query(Exchange).options(joinedload(Exchange.order)).filter(
            (Exchange.return_awb_number != None) | (Exchange.new_awb_number != None)
        ).all()

        class VirtualDelivery:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        # Use a dictionary to store deliveries keyed by order_id to prevent duplicates
        # We prioritize Exchange shipments over original deliveries
        delivery_map = {}

        # 1. Add original deliveries first
        for d in deliveries:
            # # Resolve email for delivery
            # d_email = d.order.email if d.order else None
            # if not d_email or 'example.com' in d_email:
            #     try:
            #          from app.modules.orders.models import B2CApplication
            #          if d.phone:
            #              clean = d.phone.replace("+91", "").strip()[-10:]
            #              b2c = db.query(B2CApplication).filter((B2CApplication.phone_number == clean) | (B2CApplication.phone_number == f"+91{clean}")).first()
            #              if b2c and b2c.email: d_email = b2c.email
            #     except: pass
            # d.email = d_email

            # Use order_id as key if available, otherwise use delivery id (unique)
            key = d.order_id if d.order_id else f"del_{d.id}"
            delivery_map[key] = d

        for ex in exchanges:
            if not ex.order:
                continue
            
            # Key for this order (Integer ID)
            key = ex.order.id
            
            # 1. Return Shipment (Customer -> Warehouse)
            if ex.return_awb_number:
                delivery_map[key] = VirtualDelivery(
                    id=ex.id + 50000, # Offset to avoid ID collision
                    order_id=ex.order.id,
                    order=ex.order,
                    weight=0, length=0, breadth=0, height=0,
                    awb_number=ex.return_awb_number,
                    courier_partner="Delhivery",
                    pickup_location="Customer Return",
                    payment="Prepaid",
                    amount=0,
                    customer_name=ex.customer_name,
                    # email=ex.order.email if ex.order else None,
                    phone=ex.order.phone if ex.order else "",
                    full_address=ex.order.address if ex.order else "",
                    city=ex.order.city if ex.order else "",
                    state=ex.order.state if ex.order else "",
                    pincode=ex.order.pincode if ex.order else "",
                    item_name=f"Return: {ex.product_name}",
                    quantity=ex.quantity,
                    schedule_pickup=None,
                    delivery_status=ex.return_delivery_status or "Pending",
                    awb_label_path=ex.return_label_path,
                    created_at=ex.created_at,
                    updated_at=ex.updated_at
                )

            # 2. New Shipment (Warehouse -> Customer)
            # This will overwrite the Return shipment if both exist, showing the latest stage
            if ex.new_awb_number:
                delivery_map[key] = VirtualDelivery(
                    id=ex.id + 60000, # Offset
                    order_id=ex.order.id,
                    order=ex.order,
                    weight=0, length=0, breadth=0, height=0,
                    awb_number=ex.new_awb_number,
                    courier_partner="Delhivery",
                    pickup_location="Warehouse",
                    payment="Prepaid",
                    amount=0,
                    customer_name=ex.customer_name,
                    # email=ex.order.email if ex.order else None,
                    phone=ex.order.phone if ex.order else "",
                    full_address=ex.order.address if ex.order else "",
                    city=ex.order.city if ex.order else "",
                    state=ex.order.state if ex.order else "",
                    pincode=ex.order.pincode if ex.order else "",
                    item_name=f"Exchange: {ex.product_name}",
                    quantity=ex.quantity,
                    schedule_pickup=None,
                    delivery_status=ex.new_delivery_status or "Pending",
                    awb_label_path=ex.new_label_path,
                    created_at=ex.created_at,
                    updated_at=ex.updated_at
                )
        
        deliveries = list(delivery_map.values())

        
        logger.info(f"[DELIVERIES] Total deliveries before filter: {len(deliveries)}")
        
        # Apply filters if provided
        if city:
            # Case-insensitive city filter - INCLUDE this city (skip NULL cities)
            original_count = len(deliveries)
            deliveries = [d for d in deliveries if d.city and d.city.lower() == city.lower()]
            logger.info(f"[DELIVERIES] Filter city='{city}': {original_count} → {len(deliveries)} deliveries")
        
        if exclude_city:
            # Case-insensitive city filter - EXCLUDE this city (include NULL cities)
            original_count = len(deliveries)
            deliveries = [d for d in deliveries if not (d.city and d.city.lower() == exclude_city.lower())]
            logger.info(f"[DELIVERIES] Filter exclude_city='{exclude_city}': {original_count} → {len(deliveries)} deliveries")
        
        if delivery_status:
            # Case-insensitive delivery status filter
            original_count = len(deliveries)
            deliveries = [d for d in deliveries if d.delivery_status and d.delivery_status.upper() == delivery_status.upper()]
            logger.info(f"[DELIVERIES] Filter delivery_status='{delivery_status}': {original_count} → {len(deliveries)} deliveries")

        if min_status:
            # Filter by minimum status (progression)
            # Define the logical order of statuses
            STATUS_ORDER = [
                "READY TO PICKUP",
                "PICKUP TIME SCHEDULED",
                "AWB GENERATED",
                "PICKED_UP",
                "IN_TRANSIT",
                "OUT_FOR_DELIVERY",
                "DELIVERED",
                "RTO",
                "RETURNED TO ORIGIN",
                "FAILED",
                "LOST"
            ]
            
            try:
                # Normalize min_status
                target_status = min_status.upper().replace("_", " ")
                
                # Handle "PICKED UP" vs "PICKED_UP" variation
                if target_status == "PICKED UP": target_status = "PICKED_UP"
                
                # Find index of target status
                # We need to be flexible with matching
                target_index = -1
                for i, s in enumerate(STATUS_ORDER):
                    if s.replace("_", " ") == target_status:
                        target_index = i
                        break
                
                if target_index != -1:
                    original_count = len(deliveries)
                    filtered = []
                    for d in deliveries:
                        if not d.delivery_status: continue
                        
                        current_status = d.delivery_status.upper().replace("_", " ")
                        if current_status == "PICKED UP": current_status = "PICKED_UP"
                        
                        # Find index of current status
                        current_index = -1
                        for i, s in enumerate(STATUS_ORDER):
                            if s.replace("_", " ") == current_status:
                                current_index = i
                                break
                        
                        # If found and >= target, keep it
                        if current_index >= target_index:
                            filtered.append(d)
                        # Also keep if it's not in the list? No, safer to exclude unknown if filtering by stage.
                        # But let's assume unknown statuses might be important, so maybe log them.
                        # For now, strict filtering based on known flow.
                    
                    deliveries = filtered
                    logger.info(f"[DELIVERIES] Filter min_status='{min_status}': {original_count} → {len(deliveries)} deliveries")
            except Exception as e:
                logger.error(f"[DELIVERIES] Error applying min_status filter: {e}")

        result = []
        for d in deliveries:
            tax_meta = service.get_order_tax_meta(d.order) if d.order else {
                "gst_type": "intra",
                "seller_gstin": None,
                "igst_percentage": 0.0,
            }
            # Convert to dict to append extra fields not in DB model but in Schema
            d_dict = {
                "id": d.id,
                "order_id": d.order_id,
                "weight": d.weight,
                "length": d.length,
                "breadth": d.breadth,
                "height": d.height,
                "awb_number": d.awb_number,
                "courier_partner": d.courier_partner,
                "pickup_location": d.pickup_location,
                "payment": d.payment,
                "amount": d.amount,
                "customer_name": d.customer_name,
                "phone": d.phone,
                "full_address": d.full_address,
                "city": d.city,
                "state": d.state,
                "pincode": d.pincode,
                "item_name": d.item_name,
                "quantity": d.quantity,
                "schedule_pickup": d.schedule_pickup,
                "delivery_status": d.delivery_status,
                "awb_label_path": d.awb_label_path,
                "created_at": d.created_at,
                "updated_at": d.updated_at,
                "order_number": d.order.order_id if d.order else None,
                "sgst_percentage": float(d.order.sgst_percentage) if d.order and d.order.sgst_percentage is not None else 0.0,
                "cgst_percentage": float(d.order.cgst_percentage) if d.order and d.order.cgst_percentage is not None else 0.0,
                "igst_percentage": tax_meta["igst_percentage"],
                "gst_type": tax_meta["gst_type"],
                "seller_gstin": tax_meta["seller_gstin"],
            }
            result.append(d_dict)
            
        return result
    except Exception as e:
        logger.exception("[DELIVERIES] Error fetching deliveries")
        raise HTTPException(status_code=500, detail=str(e))



@router.put("/deliveries/{delivery_id}/schedule", response_model=schemas.DeliveryResponse)
def update_delivery_schedule(delivery_id: int, schedule: schemas.DeliveryScheduleUpdate, db: Session = Depends(get_db)):
    """Update delivery schedule time"""
    delivery = service.update_delivery_schedule(db, delivery_id, schedule.schedule_pickup)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    # Construct response
    tax_meta = service.get_order_tax_meta(delivery.order) if delivery.order else {
        "gst_type": "intra",
        "seller_gstin": None,
        "igst_percentage": 0.0,
    }
    d_dict = {
        "id": delivery.id,
        "order_id": delivery.order_id,
        "weight": delivery.weight,
        "length": delivery.length,
        "breadth": delivery.breadth,
        "height": delivery.height,
        "awb_number": delivery.awb_number,
        "courier_partner": delivery.courier_partner,
        "pickup_location": delivery.pickup_location,
        "payment": delivery.payment,
        "amount": delivery.amount,
        "customer_name": delivery.customer_name,
        "phone": delivery.phone,
        "full_address": delivery.full_address,
        "city": delivery.city,
        "state": delivery.state,
        "pincode": delivery.pincode,
        "item_name": delivery.item_name,
        "quantity": delivery.quantity,
        "schedule_pickup": delivery.schedule_pickup,
        "delivery_status": delivery.delivery_status,
        "created_at": delivery.created_at,
        "updated_at": delivery.updated_at,
        "order_number": delivery.order.order_id if delivery.order else None,
        "sgst_percentage": float(delivery.order.sgst_percentage) if delivery.order and delivery.order.sgst_percentage is not None else 0.0,
        "cgst_percentage": float(delivery.order.cgst_percentage) if delivery.order and delivery.order.cgst_percentage is not None else 0.0,
        "igst_percentage": tax_meta["igst_percentage"],
        "gst_type": tax_meta["gst_type"],
        "seller_gstin": tax_meta["seller_gstin"],
    }
    return d_dict

@router.get("/{order_id}", response_model=schemas.OrderResponse)
def read_order(order_id: str, db: Session = Depends(get_db)):
    """Get specific order details with customer name"""
    order = service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Prepare response with customer_name
    # Resolve missing email
    resolve_email = order.email
    if not resolve_email or 'example.com' in resolve_email:
        try:
            from app.modules.orders.models import B2CApplication
            if order.phone:
                # Flexible phone search
                clean_phone = order.phone.replace('+91', '').replace(' ', '').strip()[-10:]
                b2c = db.query(B2CApplication).filter(
                    (B2CApplication.phone_number == clean_phone) |
                    (B2CApplication.phone_number == f"+91{clean_phone}") |
                    (B2CApplication.phone_number == order.phone)
                ).first()
                if b2c and b2c.email:
                    resolve_email = b2c.email
        except Exception:
            pass

    order_dict = {
        "id": order.id,
        "order_id": order.order_id,
        "order_number": order.order_id,
        "razorpay_order_id": getattr(order, "razorpay_order_id", None),
        "gst_type": service.get_order_tax_meta(order)["gst_type"],
        "seller_gstin": service.get_order_tax_meta(order)["seller_gstin"],
        "igst_percentage": service.get_order_tax_meta(order)["igst_percentage"],
        "customer_type": order.customer_type,
        "customer_name": order.customer_name, # Direct access
        "user_id": None,
        "products": order.products,
        "amount": float(order.amount) if order.amount else None,
        "payment": order.payment,
        "status": order.status,
        "awb_number": order.awb_number,
        "address": order.address,
        "email": resolve_email,
        "phone": order.phone,
        "city": order.city,
        "state": order.state,
        "pincode": order.pincode,
        "height": order.height,
        "weight": order.weight,
        "breadth": order.breadth,
        "length": order.length,
        "sgst_percentage": float(order.sgst_percentage) if order.sgst_percentage is not None else 0.0,
        "cgst_percentage": float(order.cgst_percentage) if order.cgst_percentage is not None else 0.0,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }
    
    return order_dict

@router.put("/{order_id}/status", response_model=schemas.OrderResponse)
def update_order_status(
    order_id: str, 
    status_update: schemas.OrderStatusUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_employee)
):
    """Update order status"""
    try:
        order = service.update_order_status(db, order_id, status_update.status)
    except Exception as e:
        # 🔥 ADD THIS (do not crash the API)
        logger.exception(f"[ROUTER] Error while updating order status for {order_id}")
        # Continue instead of failing hard
        order = service.get_order_by_id(db, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    updated_order = service.get_order_by_id(db, order_id)
    
    # Log activity
    log_activity(
        db=db,
        action="Updated Order Status",
        module="Orders",
        user_id=str(current_user.id),
        user_name=current_user.name,
        user_type=current_user.role.capitalize(),
        details=f"Changed order {order_id} status to '{status_update.status}'",
        status="Success",
        affected_entity_type="Order",
        affected_entity_id=order_id
    )
    
    order_dict = {
        "id": updated_order.id,
        "order_id": updated_order.order_id,
        "order_number": updated_order.order_id,
        "razorpay_order_id": getattr(updated_order, "razorpay_order_id", None),
        "gst_type": service.get_order_tax_meta(updated_order)["gst_type"],
        "seller_gstin": service.get_order_tax_meta(updated_order)["seller_gstin"],
        "igst_percentage": service.get_order_tax_meta(updated_order)["igst_percentage"],
        "customer_type": updated_order.customer_type,
        "customer_name": updated_order.customer_name, # Direct access
        "user_id": None,
        "products": updated_order.products,
        "amount": float(updated_order.amount) if updated_order.amount else None,
        "payment": updated_order.payment,
        "status": updated_order.status,
        "awb_number": updated_order.awb_number,
        "address": updated_order.address,
        "email": updated_order.email,
        "phone": updated_order.phone,
        "city": updated_order.city,
        "state": updated_order.state,
        "pincode": updated_order.pincode,
        "height": updated_order.height,
        "weight": updated_order.weight,
        "breadth": updated_order.breadth,
        "length": updated_order.length,
        "sgst_percentage": float(updated_order.sgst_percentage) if updated_order.sgst_percentage is not None else 0.0,
        "cgst_percentage": float(updated_order.cgst_percentage) if updated_order.cgst_percentage is not None else 0.0,
        "created_at": updated_order.created_at,
        "updated_at": updated_order.updated_at,
    }
            
    return order_dict


@router.put("/{order_id}/dimensions", response_model=schemas.OrderResponse)
def update_order_dimensions(order_id: str, dimensions: schemas.OrderDimensionsUpdate, db: Session = Depends(get_db)):
    """Update order dimensions"""
    order = service.update_order_dimensions(
        db, 
        order_id, 
        dimensions.height, 
        dimensions.weight, 
        dimensions.breadth, 
        dimensions.length
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Re-fetch to construct response
    updated_order = service.get_order_by_id(db, order_id)
    
    order_dict = {
        "id": updated_order.id,
        "order_id": updated_order.order_id,
        "order_number": updated_order.order_id,
        "razorpay_order_id": getattr(updated_order, "razorpay_order_id", None),
        "gst_type": service.get_order_tax_meta(updated_order)["gst_type"],
        "seller_gstin": service.get_order_tax_meta(updated_order)["seller_gstin"],
        "igst_percentage": service.get_order_tax_meta(updated_order)["igst_percentage"],
        "customer_type": updated_order.customer_type,
        "customer_name": updated_order.customer_name, # Direct access
        "user_id": None,
        "products": updated_order.products,
        "amount": float(updated_order.amount) if updated_order.amount else None,
        "payment": updated_order.payment,
        "status": updated_order.status,
        "awb_number": updated_order.awb_number,
        "address": updated_order.address,
        "email": updated_order.email,
        "phone": updated_order.phone,
        "city": updated_order.city,
        "state": updated_order.state,
        "pincode": updated_order.pincode,
        "height": updated_order.height,
        "weight": updated_order.weight,
        "breadth": updated_order.breadth,
        "length": updated_order.length,
        "sgst_percentage": float(updated_order.sgst_percentage) if updated_order.sgst_percentage is not None else 0.0,
        "cgst_percentage": float(updated_order.cgst_percentage) if updated_order.cgst_percentage is not None else 0.0,
        "created_at": updated_order.created_at,
        "updated_at": updated_order.updated_at,
    }
            
    return order_dict


@router.post("/bulk-generate-awb")
def bulk_generate_awb(order_ids: List[str], db: Session = Depends(get_db)):
    """
    Generate AWB labels for multiple orders in ONE Delhivery API call.
    Accepts a list of order_ids (string order_id, e.g. "ORD_123").
    Returns success/failed summary.
    """
    try:
        from app.modules.delivery.shipment_service import create_bulk_shipments_for_orders
        from app.modules.orders.models import Order

        if not order_ids:
            raise HTTPException(status_code=400, detail="No order IDs provided")

        if len(order_ids) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 orders per bulk request")

        # Fetch all orders from DB
        orders = db.query(Order).filter(Order.order_id.in_(order_ids)).all()

        if not orders:
            raise HTTPException(status_code=404, detail="No orders found for given IDs")

        logger.info(f"[BULK AWB] Generating AWB for {len(orders)} orders: {order_ids}")

        # Run bulk shipment creation
        results = create_bulk_shipments_for_orders(db, orders)

        return {
            "message": f"Bulk AWB generation complete",
            "total_requested": len(order_ids),
            "success_count": len(results["success"]),
            "failed_count": len(results["failed"]),
            "success": results["success"],
            "failed": results["failed"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[BULK AWB] Error during bulk AWB generation")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-download-awb")
def bulk_download_awb_labels(order_ids: List[str], db: Session = Depends(get_db)):
    """
    Merge multiple AWB label PDFs into a single file for bulk download
    """
    try:

        from app.modules.orders.models import Delivery
        
        # Get deliveries with AWB labels for the selected orders
        deliveries_with_labels = []
        
        for order_id in order_ids:
            order = service.get_order_by_id(db, order_id)
            if not order:
                continue
            
            # Find delivery for this order
            delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
            
            if delivery and delivery.awb_label_path:
                deliveries_with_labels.append({
                    'order_id': order.order_id,
                    'label_path': delivery.awb_label_path
                })
        
        if not deliveries_with_labels:
            logger.warning(f"No AWB labels found for order IDs: {order_ids}")
            raise HTTPException(status_code=404, detail="No AWB labels found for selected orders")
        
        # Create merger
        merger = PdfMerger()
        added_count = 0
        
        # Add each PDF to the merger
        for item in deliveries_with_labels:
            # Construct full path
            label_path = item['label_path']
            if label_path.startswith('/'):
                label_path = label_path[1:]  # Remove leading slash
            
            # Use BASE_DIR instead of os.getcwd() for production compatibility
            full_path = os.path.join(BASE_DIR, label_path)
            
            logger.info(f"Checking for AWB label at: {full_path}")
            
            if os.path.exists(full_path):
                try:
                    merger.append(full_path)
                    added_count += 1
                    logger.info(f"Added {item['order_id']} label to merge")
                except Exception as e:
                    logger.error(f"Error adding {item['order_id']} to merger: {e}")
            else:
                logger.warning(f"Label file not found: {full_path}")
        
        if added_count == 0:
            raise HTTPException(status_code=404, detail="No valid AWB label files found")
        
        # Create output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"AWB_Labels_Bulk_{timestamp}.pdf"
        output_path = os.path.join("static", "temp", output_filename)
        
        # Ensure temp directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write merged PDF
        merger.write(output_path)
        merger.close()
        
        logger.info(f"Created merged PDF with {added_count} labels: {output_path}")
        
        # Return the file
        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating bulk AWB download")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-download-invoice")
def bulk_download_invoice_labels(order_ids: List[str], db: Session = Depends(get_db)):
    """
    Merge multiple invoice label PDFs into a single file for bulk download
    """
    try:
        from app.modules.orders.label_generator import generate_invoice_label_pdf
        
        # Get orders with invoice labels for the selected orders
        orders_with_labels = []
        temp_files = []  # Track temporary files for cleanup
        
        for order_id in order_ids:
            order = service.get_order_by_id(db, order_id)
            if not order:
                continue
            
            # Prepare order data for label generation
            order_data = {
                "id": order.order_id,
                "awb_number": order.awb_number,
                "customer": order.customer_name,
                "address": order.address,
                "city": order.city,
                "state": order.state,
                "pincode": order.pincode,
                "phone": order.phone,
                "date": order.created_at.strftime('%Y-%m-%d') if order.created_at else "",
            }
            
            # Generate invoice label PDF
            # BASE_DIR is app/, go up to backend/
            output_dir = os.path.join(BASE_DIR.parent, "uploads", "invoice_labels")
            os.makedirs(output_dir, exist_ok=True)
            
            try:
                filename = generate_invoice_label_pdf(order_data, output_dir)
                label_path = os.path.join(output_dir, filename)
                
                if os.path.exists(label_path):
                    orders_with_labels.append({
                        'order_id': order.order_id,
                        'label_path': label_path
                    })
                    temp_files.append(label_path)
            except Exception as e:
                logger.error(f"Error generating invoice label for {order_id}: {e}")
                continue
        
        if not orders_with_labels:
            logger.warning(f"No invoice labels generated for order IDs: {order_ids}")
            raise HTTPException(status_code=404, detail="No invoice labels could be generated for selected orders")
        
        # Create merger
        merger = PdfMerger()
        added_count = 0
        
        # Add each PDF to the merger
        for item in orders_with_labels:
            label_path = item['label_path']
            
            if os.path.exists(label_path):
                try:
                    merger.append(label_path)
                    added_count += 1
                    logger.info(f"Added {item['order_id']} invoice label to merge")
                except Exception as e:
                    logger.error(f"Error adding {item['order_id']} to merger: {e}")
            else:
                logger.warning(f"Invoice label file not found: {label_path}")
        
        if added_count == 0:
            raise HTTPException(status_code=404, detail="No valid invoice label files found")
        
        # Create output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"Invoice_Labels_Bulk_{timestamp}.pdf"
        output_path = os.path.join("static", "temp", output_filename)
        
        # Ensure temp directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write merged PDF
        merger.write(output_path)
        merger.close()
        
        logger.info(f"Created merged invoice PDF with {added_count} labels: {output_path}")
        
        # Return the file
        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating bulk invoice download")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{order_id}/generate-invoice-label")
def generate_label(order_id: str, db: Session = Depends(get_db)):
    """Generate and return invoice label PDF"""
    order = service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    from app.modules.orders.label_generator import generate_invoice_label_pdf
    
    # Prepare data dictionary for generator
    order_data = {
        "id": order.order_id,
        "order_id": order.order_id,  # Add this for label_generator compatibility
        "razorpay_order_id": getattr(order, "razorpay_order_id", None),
        "awb_number": order.awb_number,
        "customer": order.customer_name,
        "address": order.address,
        "city": order.city,
        "state": order.state,
        "pincode": order.pincode,
        "phone": order.phone,
        "date": order.created_at.strftime('%Y-%m-%d') if order.created_at else "",
        "amount": float(order.amount) if order.amount else 0.0,
    }
    
    # Define output directory with absolute path
    # BASE_DIR is app/, we need to go up one level to backend/ to store in backend/uploads/
    output_dir = os.path.join(BASE_DIR.parent, "uploads", "invoice_labels")
    
    logger.info(f"[INVOICE_LABEL] Generating label for order: {order_id}")
    logger.info(f"[INVOICE_LABEL] Output directory: {output_dir}")
    logger.info(f"[INVOICE_LABEL] Order data: {order_data}")
    
    try:
        filename = generate_invoice_label_pdf(order_data, output_dir)
        full_path = os.path.join(output_dir, filename)
        
        logger.info(f"[INVOICE_LABEL] Generated filename: {filename}")
        logger.info(f"[INVOICE_LABEL] Full path: {full_path}")
        logger.info(f"[INVOICE_LABEL] File exists: {os.path.exists(full_path)}")
        
        # Return URL handled by StaticFiles mount
        return {"url": f"/uploads/invoice_labels/{filename}"}
    except Exception as e:
        logger.exception(f"[INVOICE_LABEL] Failed to generate label for {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}/awb/download")
def download_awb_label(order_id: str, db: Session = Depends(get_db)):
    """Download AWB label PDF, fetching from Delhivery if missing"""
    from fastapi.responses import FileResponse, Response
    
    order = service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    awb_number = order.awb_number
    if not awb_number:
        raise HTTPException(status_code=400, detail="AWB not generated yet")

    from app.modules.orders.models import Delivery
    delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
    
    # 1. Check if we already have it locally
    awb_path = None
    if delivery and delivery.awb_label_path:
        awb_path = os.path.join(BASE_DIR.parent, delivery.awb_label_path.lstrip('/'))
        if os.path.exists(awb_path):
            return FileResponse(
                path=awb_path,
                filename=f"AWB_{awb_number}.pdf",
                media_type="application/pdf"
            )

    # 2. Fetch from Delhivery
    from app.modules.delivery.delhivery_client import delhivery_client
    pdf_content, err = delhivery_client.fetch_awb_label(awb_number)
    
    if pdf_content:
        # Save it locally for future hits
        try:
            output_dir = os.path.join(BASE_DIR.parent, "uploads", "awb")
            os.makedirs(output_dir, exist_ok=True)
            filename = f"awb_{awb_number}.pdf"
            local_path = os.path.join(output_dir, filename)
            
            with open(local_path, "wb") as f:
                f.write(pdf_content)
                
            if delivery:
                delivery.awb_label_path = f"/uploads/awb/{filename}"
                db.commit()
                
            return Response(
                content=pdf_content, 
                media_type="application/pdf", 
                headers={"Content-Disposition": f"attachment; filename=AWB_{awb_number}.pdf"}
            )
        except Exception as e:
            logger.error(f"Failed to save fetched AWB {awb_number}: {e}")
            return Response(
                content=pdf_content, 
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=AWB_{awb_number}.pdf"}
            )
            
    logger.error(f"Failed to fetch AWB from Delhivery: {err}")
    raise HTTPException(status_code=404, detail="AWB label not found on Delhivery servers")

@router.post("/{order_id}/email-invoice")
def email_invoice_endpoint(order_id: str, db: Session = Depends(get_db)):
    """Manually generate and email commercial invoice"""
    order = service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    try:
        from app.modules.orders.invoice_generator import generate_invoice_pdf
        from app.modules.auth.sendgrid_utils import sendgrid_service
        import os

        # FIX: Resolve placeholder email from B2C Records
        if not order.email or 'example.com' in order.email or not order.email.strip():
            try:
                from app.modules.orders.models import B2CApplication
                if order.phone:
                    # Search by phone in B2C App
                    b2c_user = db.query(B2CApplication).filter(B2CApplication.phone_number == order.phone).first()
                    if b2c_user and b2c_user.email:
                        logger.info(f"Fixed missing email for Order {order.order_id}: {order.email} -> {b2c_user.email}")
                        order.email = b2c_user.email
                        db.commit() # Persist the fix
            except Exception as e:
                logger.warning(f"Email resolution failed: {e}")
        
        inv_dir = os.path.join("uploads", "invoices")
        # Generate
        filename = generate_invoice_pdf(order, inv_dir)
        filepath = os.path.join(inv_dir, filename)
        
        if order.email:
             sent = sendgrid_service.send_invoice_email(order.email, order.order_id, filepath)
             if sent:
                 return {"message": f"Invoice emailed to {order.email}", "url": f"/uploads/invoices/{filename}"}
             else:
                 raise HTTPException(status_code=500, detail="Failed to send email via SendGrid")
        else:
             return {"message": "Invoice generated but order has no email", "url": f"/uploads/invoices/{filename}"}
             
    except Exception as e:
        logger.exception("Failed to email invoice")
        raise HTTPException(status_code=500, detail=str(e))
