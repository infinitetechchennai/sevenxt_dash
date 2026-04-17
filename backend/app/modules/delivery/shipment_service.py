from typing import Optional
from sqlalchemy.orm import Session
from app.modules.orders.models import Order, Delivery
from app.modules.delivery.delhivery_client import delhivery_client
import logging
import re

logger = logging.getLogger(__name__)


def create_shipment_for_order(db: Session, order: Order) -> Optional[str]:
    """
    Creates a shipment in Delhivery and updates the local database with the AWB number.
    Triggered when Order status is 'Ready to Pickup'.
    """
    print(f"[DEBUG] create_shipment_for_order called for {order.order_id}")
    logger.info(
        f"[SHIPMENT] Processing shipment for order_id={order.order_id} | Status={order.status}"
    )

    # Quick check for service type (Visual only here, actual logic is below but same)
    _debug_service = "E"
    if order.weight and float(order.weight) > 10.0:
        _debug_service = "S"
        
   
    # 1. Check if AWB already exists (and is not null)
    if order.awb_number and order.awb_number.strip():
        logger.warning(f"[SHIPMENT] AWB already exists: {order.awb_number}")
        return order.awb_number

    # 2. Verify Status - REMOVED (Handled by caller)
    # The caller (update_order_status) ensures this is only called when status is 'Ready to Pickup'.
    # Removing this check allows the function to be used more flexibly (e.g., manual retries).
    pass

    # 3. Validate Required Fields
    missing_fields = []
    if not order.length: missing_fields.append("length")
    if not order.breadth: missing_fields.append("breadth")
    if not order.height: missing_fields.append("height")
    if not order.weight: missing_fields.append("weight")
    if not order.phone: missing_fields.append("phone")
    if not order.address: missing_fields.append("address")

    if missing_fields:
        msg = f"[SHIPMENT] Cannot create shipment. Missing fields: {missing_fields}"
        logger.error(msg)
        return None

    # 4. Prepare Data for Delhivery
    customer_name = order.customer_name or "Customer"

    # Use separate city, state, pincode fields (no parsing from address)
    city = order.city if (hasattr(order, 'city') and order.city) else "Chennai"
    state = order.state if (hasattr(order, 'state') and order.state) else "Tamil Nadu"
    pincode = order.pincode if (hasattr(order, 'pincode') and order.pincode) else "600018"

    # PRE-CHECK: Serviceability (Fix for missing API)
    serviceability = delhivery_client.check_pincode_serviceability(str(pincode))
    if not serviceability.get("serviceable", True):  # Fall back to True if API errors
        msg = f"[SHIPMENT] Cannot create shipment. Pincode {pincode} is not serviceable. Reason: {serviceability.get('reason')}"
        logger.error(msg)
        return None

    # Format phone number: Remove +91, -, spaces, and keep only 10 digits
    phone = order.phone or ""
    print(f"[DEBUG] Original Phone from Order: '{phone}'")
    
    phone = re.sub(r"[^\d]", "", phone)  # Remove all non-digits
    phone = phone[-10:] if len(phone) >= 10 else phone  # Take last 10 digits
    
    print(f"[DEBUG] Formatted Phone: '{phone}'")
    
    if not phone:
        msg = "[SHIPMENT] Phone number is empty or invalid after formatting"
        logger.error(msg)
        return None

    # Fetch delivery record to get item_name and quantity
    delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
    item_name = "Product"
    quantity = 1
    if delivery:
        item_name = delivery.item_name or "Product"
        quantity = delivery.quantity or 1

    # Determine Service Type (Express vs Surface)
    # Default to Express (Air)
    service_type = "E"
    
    # Rule: If weight is greater than 10kg, use Surface (Road)
    if order.weight and float(order.weight) > 10.0:
        service_type = "S"

    order_data = {
        "customer_name": customer_name,
        "address": order.address,
        "pincode": str(pincode),  # Ensure string
        "city": city,
        "state": state,
        "phone": phone,  # Already formatted as 10-digit string
        "email": order.email or "noreply@sevenxt.com",  # Add email
        "order_id": order.order_id,
        "payment_status": order.payment,
        "amount": float(order.amount) if order.amount else 0.0,
        "length": float(order.length),
        "breadth": float(order.breadth),
        "height": float(order.height),
        "weight": float(order.weight),
        "item_name": item_name,
        "quantity": quantity,
        "service_type": service_type,
        "hsn_code": order.hsn or "",
    }

    logger.info(f"[SHIPMENT] Payload prepared: {order_data}")

    # 5. Call Delhivery API (using centralized singleton)
    client = delhivery_client
    
    try:
        response = client.create_shipment(order_data)
        logger.info(f"[SHIPMENT] API Response: {response}")

        # Check for logical error (Delhivery returns 200 but success=False)
        if not response.get("success") and "ClientWarehouse" in str(response):
            raise Exception(f"Delhivery Logical Error: {response.get('rmk', 'ClientWarehouse error')}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"[SHIPMENT] API Call Failed: {error_msg}")
        
        # Check if it's a warehouse error
        # Note: The exact error string depends on Delhivery's response. 
        # Usually it's in the response body which might be in the exception if using requests.raise_for_status()
        # But here we just check the string representation of the exception or response text if available.
        
        is_warehouse_error = "ClientWarehouse" in error_msg or "warehouse" in error_msg.lower()
        
        if is_warehouse_error:
            logger.info("[SHIPMENT] Warehouse might be missing. Attempting to create warehouse...")
            try:
                client.create_warehouse() # Uses defaults
                logger.info("[SHIPMENT] Warehouse created. Retrying shipment creation...")
                response = client.create_shipment(order_data)
                logger.info(f"[SHIPMENT] Retry API Response: {response}")
            except Exception as retry_e:
                logger.exception(f"[SHIPMENT] Retry Failed: {retry_e}")
                return None
        else:
            return None

    if not response or "packages" not in response:
        logger.error("[SHIPMENT] Invalid response from Delhivery (no 'packages' key)")
        return None

    # 6. Extract Waybill (AWB)
    try:
        package = response["packages"][0]
        waybill = package.get("waybill")
        
        if not waybill:
            logger.error(f"[SHIPMENT] Waybill not found in package data: {package}")
            return None
            
        if package.get("status") == "Fail":
             remarks = package.get('remarks', [])
             # Check if it's a duplicate order error, which means we can still use the waybill
             is_duplicate = False
             if isinstance(remarks, list):
                 for r in remarks:
                     if "Duplicate order id" in str(r):
                         is_duplicate = True
                         break
             elif isinstance(remarks, str) and "Duplicate order id" in remarks:
                 is_duplicate = True
                 
             if is_duplicate and waybill:
                 logger.info(f"[SHIPMENT] Order already exists in Delhivery. Using existing waybill: {waybill}")
             else:
                 logger.error(f"[SHIPMENT] Delhivery returned failure: {remarks}")
                 return None

    except (IndexError, AttributeError) as e:
        logger.error(f"[SHIPMENT] Error parsing response packages: {e}")
        return None

    logger.info(f"[SHIPMENT] AWB Generated Successfully: {waybill}")

    # Generate Commercial Invoice automatically
    try:
        # Update order object with AWB for invoice generation
        order.awb_number = waybill
        
        from app.modules.orders.invoice_generator import generate_invoice_pdf
        from app.modules.auth.sendgrid_utils import sendgrid_service
        import os

        # FIX: Check for placeholder email and try to resolve from B2C Applications
        if not order.email or 'example.com' in order.email or not order.email.strip():
            try:
                from app.modules.orders.models import B2CApplication
                if order.phone:
                    # Search by phone in B2C App
                    b2c_user = db.query(B2CApplication).filter(B2CApplication.phone_number == order.phone).first()
                    if b2c_user and b2c_user.email:
                        logger.info(f"[SHIPMENT] Fixed missing email for Order {order.order_id}: {order.email} -> {b2c_user.email}")
                        order.email = b2c_user.email
                        db.add(order) 
            except Exception as e:
                logger.warning(f"[SHIPMENT] Email resolution failed: {e}")
        
        inv_dir = os.path.join("uploads", "invoices")
        inv_filename = generate_invoice_pdf(order, inv_dir)
        inv_path = os.path.join(inv_dir, inv_filename)
        logger.info(f"[SHIPMENT] Commercial Invoice generated: {inv_path}")
        
        # Send Invoice via Email
        if order.email:
             logger.info(f"[SHIPMENT] Sending Invoice Email to {order.email}")
             sent = sendgrid_service.send_invoice_email(order.email, order.order_id, inv_path)
             if sent:
                 logger.info(f"[SHIPMENT] Invoice Email Sent Successfully")
             else:
                 logger.error(f"[SHIPMENT] Invoice Email Failed to Send")
        else:
             logger.warning(f"[SHIPMENT] No customer email found for Order {order.order_id}, skipping email.")

    except Exception as inv_e:
        logger.error(f"[SHIPMENT] Failed to generate commercial invoice: {inv_e}")

    # 7. Fetch and Save Label
    awb_label_path = None
    try:
        logger.info(f"[SHIPMENT] Fetching label for AWB: {waybill}")
        pdf_content, error = client.fetch_awb_label(waybill)
        
        if pdf_content:
            import os
            # Define path
            upload_dir = os.path.join("uploads", "awb")
            os.makedirs(upload_dir, exist_ok=True)
            
            filename = f"awb_{waybill}.pdf"
            file_path = os.path.join(upload_dir, filename)
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(pdf_content)
                
            # Store relative path for DB (e.g., /uploads/awb/awb_123.pdf)
            awb_label_path = f"/uploads/awb/{filename}"
            logger.info(f"[SHIPMENT] Label saved to {file_path}")
        else:
            logger.error(f"[SHIPMENT] Failed to fetch label: {error}")

    except Exception as e:
        logger.exception(f"[SHIPMENT] Error fetching/saving label: {e}")

    # 8. Update Database (Orders & Deliveries)
    try:
        # Update Order
        order.awb_number = waybill
        order.status = "AWB_GENERATED"
        
        # Update Delivery
        delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
        if delivery:
            delivery.awb_number = waybill
            delivery.delivery_status = "AWB Generated"
            if awb_label_path:
                delivery.awb_label_path = awb_label_path
            logger.info(f"[SHIPMENT] Updated Delivery table for Order {order.order_id}")
        else:
            logger.warning(f"[SHIPMENT] Delivery record not found for Order {order.order_id}")

        db.commit()
        db.refresh(order)
        logger.info(f"[SHIPMENT] DB Updated. Flow Complete.")
        
        return waybill

    except Exception as e:
        logger.exception(f"[SHIPMENT] Database Update Failed: {e}")
        db.rollback()
        return None


# --------------------------------------------------
# BULK SHIPMENT CREATION (Multiple Orders at Once)
# --------------------------------------------------
def create_bulk_shipments_for_orders(db: Session, orders: list) -> dict:
    """
    Create AWB for multiple orders in ONE Delhivery API call.
    Returns: {"success": [...], "failed": [...]}
    """
    logger.info(f"[BULK SHIPMENT] Processing {len(orders)} orders in one API call")

    client = delhivery_client

    # 1. Prepare all valid orders — skip already processed / invalid ones
    orders_data = []
    skipped = []
    for order in orders:
        if order.awb_number and order.awb_number.strip():
            logger.warning(f"[BULK SHIPMENT] Skipping {order.order_id} — AWB already exists")
            skipped.append(order.order_id)
            continue

        if not order.address or not order.phone:
            logger.error(f"[BULK SHIPMENT] Skipping {order.order_id} — missing address/phone")
            skipped.append(order.order_id)
            continue

        # Format phone
        phone = re.sub(r"[^\d]", "", order.phone or "")
        phone = phone[-10:] if len(phone) >= 10 else phone
        if not phone:
            logger.error(f"[BULK SHIPMENT] Skipping {order.order_id} — invalid phone")
            skipped.append(order.order_id)
            continue

        city = order.city if (hasattr(order, 'city') and order.city) else "Chennai"
        state = order.state if (hasattr(order, 'state') and order.state) else "Tamil Nadu"
        pincode = order.pincode if (hasattr(order, 'pincode') and order.pincode) else "600018"

        delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
        item_name = delivery.item_name if delivery and delivery.item_name else "Product"
        quantity = delivery.quantity if delivery and delivery.quantity else 1
        service_type = "S" if (order.weight and float(order.weight) > 10.0) else "E"

        orders_data.append({
            "customer_name": order.customer_name or "Customer",
            "address": order.address,
            "pincode": str(pincode),
            "city": city,
            "state": state,
            "phone": phone,
            "email": order.email or "noreply@sevenxt.com",
            "order_id": order.order_id,
            "payment_status": order.payment,
            "amount": float(order.amount) if order.amount else 0.0,
            "length": float(order.length) if order.length else 10.0,
            "breadth": float(order.breadth) if order.breadth else 10.0,
            "height": float(order.height) if order.height else 10.0,
            "weight": float(order.weight) if order.weight else 0.5,
            "item_name": item_name,
            "quantity": quantity,
            "service_type": service_type,
        })

    if not orders_data:
        logger.warning("[BULK SHIPMENT] No valid orders to process")
        return {"success": [], "failed": skipped}

    # 2. ONE API call for ALL orders
    results = {"success": [], "failed": list(skipped)}
    try:
        response = client.create_bulk_shipment(orders_data)
        logger.info(f"[BULK SHIPMENT] API done. Packages: {len(response.get('packages', []))}")

        if "packages" not in response:
            logger.error(f"[BULK SHIPMENT] No packages in response: {response}")
            results["failed"].extend([o["order_id"] for o in orders_data])
            return results

    except Exception as e:
        logger.exception(f"[BULK SHIPMENT] API Call Failed: {e}")
        results["failed"].extend([o["order_id"] for o in orders_data])
        return results

    # 3. Process each package result
    for package in response.get("packages", []):
        waybill = package.get("waybill")
        order_id = package.get("refnum")   # Delhivery echoes back your order_id
        pkg_status = package.get("status")

        if not waybill or not order_id:
            logger.warning(f"[BULK SHIPMENT] Missing waybill/refnum: {package}")
            continue

        if pkg_status == "Fail":
            logger.error(f"[BULK SHIPMENT] {order_id} failed: {package.get('remarks')}")
            results["failed"].append(order_id)
            continue

        # Find matching order object
        order = next((o for o in orders if o.order_id == order_id), None)
        if not order:
            logger.warning(f"[BULK SHIPMENT] Order object not found for {order_id}")
            continue

        logger.info(f"[BULK SHIPMENT] AWB={waybill} for order={order_id}")

        # 4. Fetch and save AWB label PDF
        awb_label_path = None
        try:
            import os
            pdf_content, error = client.fetch_awb_label(waybill)
            if pdf_content:
                upload_dir = os.path.join("uploads", "awb")
                os.makedirs(upload_dir, exist_ok=True)
                filename = f"awb_{waybill}.pdf"
                file_path = os.path.join(upload_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(pdf_content)
                awb_label_path = f"/uploads/awb/{filename}"
                logger.info(f"[BULK SHIPMENT] Label saved: {file_path}")
        except Exception as le:
            logger.exception(f"[BULK SHIPMENT] Label fetch failed for {waybill}: {le}")

        # 5. Update DB for this order
        try:
            order.awb_number = waybill
            order.status = "AWB_GENERATED"
            delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
            if delivery:
                delivery.awb_number = waybill
                delivery.delivery_status = "AWB Generated"
                if awb_label_path:
                    delivery.awb_label_path = awb_label_path
            results["success"].append({"order_id": order_id, "waybill": waybill})
        except Exception as dbe:
            logger.exception(f"[BULK SHIPMENT] DB update failed for {order_id}: {dbe}")
            results["failed"].append(order_id)

    # 6. Commit all DB updates at once
    try:
        db.commit()
        logger.info(f"[BULK SHIPMENT] Complete. Success={len(results['success'])}, Failed={len(results['failed'])}")
    except Exception as ce:
        logger.exception(f"[BULK SHIPMENT] Commit failed: {ce}")
        db.rollback()

    return results


def create_return_shipment(db: Session, refund) -> tuple:
    """
    Creates a RETURN shipment (customer -> warehouse) for approved refund.
    Returns: (return_awb_number, return_label_path)
    """
    logger.info(f"[RETURN] Creating return shipment for refund ID: {refund.id}")
    
    order = refund.order
    
    if not order:
        logger.error(f"[RETURN] No order found for refund {refund.id}")
        return (None, None)
    
    # Validate required fields
    if not order.phone or not order.address or not order.pincode:
        logger.error(f"[RETURN] Missing customer details for return shipment")
        return (None, None)
    
    # Format phone number
    phone = re.sub(r"[^\d]", "", order.phone or "")
    phone = phone[-10:] if len(phone) >= 10 else phone
    
    if not phone:
        logger.error(f"[RETURN] Invalid phone number")
        return (None, None)
    
    # Prepare RETURN shipment data (REVERSE PICKUP: Customer → Warehouse)
    return_order_data = {
        # PICKUP POINT: Customer's Address (where courier will go to pick up)
        "customer_name": order.customer_name or "Customer",
        "address": order.address,
        "pincode": str(order.pincode),
        "city": order.city or "Unknown",
        "state": order.state or "Unknown",
        "phone": phone,
        "email": order.email or "noreply@sevenxt.com",
        
        # Order details
        "order_id": f"RETURN-{refund.id}",  # Unique return order ID
        "payment_status": "Pickup",  # CRITICAL: Triggers reverse pickup (NOT "Prepaid")
        "amount": float(refund.amount),
        
        # Package dimensions (use original order dimensions)
        "length": float(order.length) if order.length else 10.0,
        "breadth": float(order.breadth) if order.breadth else 10.0,
        "height": float(order.height) if order.height else 10.0,
        "weight": float(order.weight) if order.weight else 0.5,
        
        # Product details
        "item_name": f"Return: {refund.reason[:50]}",  # Use refund reason
        "quantity": 1,
        "service_type": "E",  # Express service for returns
    }
    
    logger.info(f"[RETURN] Payload prepared: {return_order_data}")
    
    # Call Delhivery API
    client = delhivery_client
    
    try:
        response = client.create_shipment(return_order_data)
        logger.info(f"[RETURN] API Response: {response}")
        
        if not response or "packages" not in response:
            logger.error("[RETURN] Invalid response from Delhivery")
            return (None, None)
        
        # Extract AWB
        package = response["packages"][0]
        return_awb = package.get("waybill")
        
        if not return_awb:
            logger.error(f"[RETURN] No waybill in response: {package}")
            return (None, None)
        
        # Handle duplicate order (if return was already created)
        if package.get("status") == "Fail":
            remarks = package.get('remarks', [])
            is_duplicate = any("Duplicate order id" in str(r) for r in (remarks if isinstance(remarks, list) else [remarks]))
            
            if is_duplicate and return_awb:
                logger.info(f"[RETURN] Using existing return AWB: {return_awb}")
            else:
                logger.error(f"[RETURN] Delhivery returned failure: {remarks}")
                return (None, None)
        
        logger.info(f"[RETURN] Return AWB Generated: {return_awb}")
        
        # Fetch and save return label with retry logic
        return_label_path = None
        file_path = None
        try:
            import time
            max_retries = 3
            retry_delay = 2
            
            pdf_content = None
            for attempt in range(max_retries):
                logger.info(f"[RETURN] Fetching label for AWB {return_awb} (Attempt {attempt + 1}/{max_retries})")
                pdf_content, error = client.fetch_awb_label(return_awb)
                
                if pdf_content:
                    logger.info(f"[RETURN] Label fetched successfully on attempt {attempt + 1}")
                    break
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"[RETURN] Label not ready yet, waiting {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"[RETURN] Failed to fetch label after {max_retries} attempts: {error}")
            
            if pdf_content:
                import os
                upload_dir = os.path.join("uploads", "return_awb")
                os.makedirs(upload_dir, exist_ok=True)
                
                filename = f"return_awb_{return_awb}.pdf"
                file_path = os.path.join(upload_dir, filename)
                
                with open(file_path, "wb") as f:
                    f.write(pdf_content)
                
                return_label_path = f"/uploads/return_awb/{filename}"
                logger.info(f"[RETURN] Label saved to {file_path}")
            else:
                logger.error(f"[RETURN] Failed to fetch return label after all retries")
        
        except Exception as e:
            logger.exception(f"[RETURN] Error fetching/saving label: {e}")
        
        # ALWAYS send email with AWB details (with or without label attachment)
        logger.info(f"[RETURN] Sending return label email to {order.email}")
        email_sent = send_return_label_email(
            customer_email=order.email,
            customer_name=order.customer_name or "Customer",
            awb_number=return_awb,
            label_path=file_path,  # Will be None if fetch failed
            reason=refund.reason
        )
        if email_sent:
            logger.info(f"[RETURN] ✅ Email sent successfully")
        else:
            logger.error(f"[RETURN] ❌ Failed to send email (See errors above)")
        
        return (return_awb, return_label_path)
    
    except Exception as e:
        logger.exception(f"[RETURN] Failed to create return shipment: {e}")
        return (None, None)


def send_return_label_email(customer_email: str, customer_name: str, awb_number: str, label_path: str = None, reason: str = ""):
    """
    Send return AWB label to customer via SendGrid
    If label_path is None or file doesn't exist, sends email without attachment
    """
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, From
        from app.config import settings
        import base64
        import os
        
        logger.info(f"[EMAIL] Starting email send process to {customer_email}")
        
        # Use SendGrid credentials from config
        SENDGRID_API_KEY = settings.SENDGRID_API_KEY
        SENDGRID_FROM_EMAIL = settings.SENDGRID_FROM_EMAIL
        SENDGRID_FROM_NAME = settings.SENDGRID_FROM_NAME
        
        logger.info(f"[EMAIL] Using SendGrid from: {SENDGRID_FROM_EMAIL}")
        
        # Validate email
        if not customer_email or '@' not in customer_email:
            logger.error(f"[EMAIL] Invalid customer email: {customer_email}")
            return False
        
        # Check if we have a valid label file
        has_label = label_path and os.path.exists(label_path)
        
        if has_label:
            logger.info(f"[EMAIL] Label file found: {label_path}")
        else:
            logger.warning(f"[EMAIL] No label file available, sending email without attachment")
        
        # Prepare email content based on whether we have a label
        if has_label:
            email_body = f'''
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #4F46E5;">Your Return Request Has Been Approved</h2>
                        
                        <p>Dear {customer_name},</p>
                        
                        <p>Your refund request has been approved. Please find your return shipping label attached to this email.</p>
                        
                        <div style="background-color: #F3F4F6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="margin-top: 0;">Return Details:</h3>
                            <p><strong>Return AWB Number:</strong> {awb_number}</p>
                            <p><strong>Reason:</strong> {reason}</p>
                        </div>
                        
                        <h3>Next Steps:</h3>
                        <ol>
                            <li>Print the attached return label</li>
                            <li>Pack the item securely in its original packaging</li>
                            <li>Attach the return label to the package</li>
                            <li>Our delivery partner will pick up the package from your address</li>
                        </ol>
                        
                        <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #E5E7EB;">
                            <strong>Need Help?</strong><br>
                            Contact us at support@sevenxt.com
                        </p>
                        
                        <p style="color: #6B7280; font-size: 12px; margin-top: 20px;">
                            This is an automated email. Please do not reply to this message.
                        </p>
                    </div>
                </body>
            </html>
            '''
        else:
            email_body = f'''
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #4F46E5;">Your Return Request Has Been Approved</h2>
                        
                        <p>Dear {customer_name},</p>
                        
                        <p>Your refund request has been approved. Your return AWB number has been generated.</p>
                        
                        <div style="background-color: #F3F4F6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="margin-top: 0;">Return Details:</h3>
                            <p><strong>Return AWB Number:</strong> {awb_number}</p>
                            <p><strong>Reason:</strong> {reason}</p>
                        </div>
                        
                        <div style="background-color: #FEF3C7; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #F59E0B;">
                            <p style="margin: 0;"><strong>Note:</strong> Your return label is being generated and will be sent to you shortly in a separate email. You can also contact our support team at support@sevenxt.com to get your return label.</p>
                        </div>
                        
                        <h3>Next Steps:</h3>
                        <ol>
                            <li>Wait for the return label email (or contact support)</li>
                            <li>Print the return label</li>
                            <li>Pack the item securely in its original packaging</li>
                            <li>Attach the return label to the package</li>
                            <li>Our delivery partner will pick up the package from your address</li>
                        </ol>
                        
                        <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #E5E7EB;">
                            <strong>Need Help?</strong><br>
                            Contact us at support@sevenxt.com with your AWB number: {awb_number}
                        </p>
                        
                        <p style="color: #6B7280; font-size: 12px; margin-top: 20px;">
                            This is an automated email. Please do not reply to this message.
                        </p>
                    </div>
                </body>
            </html>
            '''
        
        # Create email
        message = Mail(
            from_email=From(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
            to_emails=customer_email,
            subject=f'Return Label for Your Refund Request - AWB: {awb_number}',
            html_content=email_body
        )
        
        # Add attachment only if we have a valid label file
        if has_label:
            try:
                # Read the PDF file
                logger.info(f"[EMAIL] Reading label file: {label_path}")
                with open(label_path, 'rb') as f:
                    pdf_data = f.read()
                
                logger.info(f"[EMAIL] PDF file size: {len(pdf_data)} bytes")
                
                # Encode to base64
                encoded_file = base64.b64encode(pdf_data).decode()
                
                # Create attachment
                attached_file = Attachment(
                    FileContent(encoded_file),
                    FileName(f'return_label_{awb_number}.pdf'),
                    FileType('application/pdf'),
                    Disposition('attachment')
                )
                
                message.add_attachment(attached_file)
                logger.info(f"[EMAIL] Attachment added successfully")
            except Exception as attach_error:
                logger.error(f"[EMAIL] Failed to attach label, sending email without it: {attach_error}")
        
        logger.info(f"[EMAIL] Email message created, sending via SendGrid...")
        
        # Send email
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"[EMAIL] ✅ Return label email sent successfully to {customer_email}. Status: {response.status_code}")
        logger.info(f"[EMAIL] Response headers: {response.headers}")
        
        return True
        
    except Exception as e:
        logger.exception(f"[EMAIL] ❌ Failed to send return label email: {e}")
        logger.error(f"[EMAIL] Error type: {type(e).__name__}")
        logger.error(f"[EMAIL] Error details: {str(e)}")
        return False


def create_exchange_return_shipment(db: Session, exchange) -> tuple:
    """
    Creates a RETURN shipment (customer → warehouse) for approved exchange.
    Returns: (return_awb_number, return_label_path)
    """
    logger.info(f"[EXCHANGE] Creating return shipment for exchange ID: {exchange.id}")
    
    order = exchange.order
    
    if not order:
        logger.error(f"[EXCHANGE] No order found for exchange {exchange.id}")
        return (None, None)
    
    # Validate required fields
    if not order.phone or not order.address or not order.pincode:
        logger.error(f"[EXCHANGE] Missing customer details for return shipment")
        return (None, None)
    
    # Format phone number
    phone = re.sub(r"[^\d]", "", order.phone or "")
    phone = phone[-10:] if len(phone) >= 10 else phone
    
    if not phone:
        logger.error(f"[EXCHANGE] Invalid phone number")
        return (None, None)
    
    # Prepare RETURN shipment data (REVERSE PICKUP: Customer → Warehouse)
    return_order_data = {
        # PICKUP POINT: Customer's Address (where courier will go to pick up)
        "customer_name": order.customer_name or "Customer",
        "address": order.address,
        "pincode": str(order.pincode),
        "city": order.city or "Unknown",
        "state": order.state or "Unknown",
        "phone": phone,
        "email": order.email or "noreply@sevenxt.com",
        
        # Order details
        "order_id": f"EXCH-RET-{exchange.id}",  # Unique return order ID for exchange
        "payment_status": "Pickup",  # CRITICAL: Triggers reverse pickup (NOT "Prepaid")
        "amount": float(exchange.price) if exchange.price else 0.0,
        
        # Package dimensions (use original order dimensions or defaults)
        "length": float(order.length) if order.length else 10.0,
        "breadth": float(order.breadth) if order.breadth else 10.0,
        "height": float(order.height) if order.height else 10.0,
        "weight": float(order.weight) if order.weight else 0.5,
        
        # Product details
        "item_name": f"Exchange Return: {exchange.product_name}",
        "quantity": exchange.quantity,
        "service_type": "E",
    }
    
    logger.info(f"[EXCHANGE] Return Payload prepared: {return_order_data}")
    
    client = delhivery_client
    
    try:
        response = client.create_shipment(return_order_data)
        logger.info(f"[EXCHANGE] API Response: {response}")
        
        if not response or "packages" not in response:
            logger.error("[EXCHANGE] Invalid response from Delhivery")
            return (None, None)
        
        package = response["packages"][0]
        return_awb = package.get("waybill")
        
        if not return_awb:
            # Check for duplicate
            if package.get("status") == "Fail":
                 remarks = package.get('remarks', [])
                 is_duplicate = any("Duplicate order id" in str(r) for r in (remarks if isinstance(remarks, list) else [remarks]))
                 if is_duplicate:
                     # In a real scenario, we might need to fetch the existing waybill if not returned
                     # For now, we log it. Delhivery usually returns the waybill even on duplicate error if 'sort_code' is present, but not always.
                     logger.warning(f"[EXCHANGE] Duplicate return order. Waybill might be missing.")
            
            if not return_awb:
                logger.error(f"[EXCHANGE] No waybill in response: {package}")
                return (None, None)
        
        logger.info(f"[EXCHANGE] Return AWB Generated: {return_awb}")
        
        # Fetch label with retry logic (Delhivery might take a few seconds to generate label)
        return_label_path = None
        try:
            import time
            max_retries = 3
            retry_delay = 2  # seconds
            
            pdf_content = None
            for attempt in range(max_retries):
                logger.info(f"[EXCHANGE] Fetching label for AWB {return_awb} (Attempt {attempt + 1}/{max_retries})")
                pdf_content, error = client.fetch_awb_label(return_awb)
                
                if pdf_content:
                    logger.info(f"[EXCHANGE] Label fetched successfully on attempt {attempt + 1}")
                    break
                else:
                    if attempt < max_retries - 1:  # Don't sleep on last attempt
                        logger.warning(f"[EXCHANGE] Label not ready yet, waiting {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"[EXCHANGE] Failed to fetch label after {max_retries} attempts: {error}")
            
            if pdf_content:
                import os
                upload_dir = os.path.join("uploads", "return_awb")
                os.makedirs(upload_dir, exist_ok=True)
                filename = f"exchange_return_{return_awb}.pdf"
                file_path = os.path.join(upload_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(pdf_content)
                return_label_path = f"/uploads/return_awb/{filename}"
                
                # Send email
                send_return_label_email(order.email, order.customer_name, return_awb, file_path, f"Exchange Request: {exchange.reason}")
            else:
                logger.warning(f"[EXCHANGE] Proceeding without label - will need to fetch manually later")
        except Exception as e:
            logger.exception(f"[EXCHANGE] Error fetching/saving label: {e}")
            
        return (return_awb, return_label_path)
        
    except Exception as e:
        logger.exception(f"[EXCHANGE] Failed to create return shipment: {e}")
        return (None, None)


def create_exchange_forward_shipment(db: Session, exchange) -> tuple:
    """
    Creates a NEW forward shipment for the replacement item.
    Updates Exchange with new_awb and Order with awb_number (overwriting old).
    Returns: (new_awb_number, new_label_path)
    """
    logger.info(f"[EXCHANGE] Creating forward shipment for exchange ID: {exchange.id}")
    
    order = exchange.order
    if not order:
        return (None, None)
        
    # Prepare Forward Shipment Data
    # Similar to create_shipment_for_order but with new Order ID suffix to avoid duplicate
    
    # Format phone
    phone = re.sub(r"[^\d]", "", order.phone or "")
    phone = phone[-10:] if len(phone) >= 10 else phone
    
    order_data = {
        "customer_name": order.customer_name or "Customer",
        "address": order.address,
        "pincode": str(order.pincode),
        "city": order.city or "Chennai",
        "state": order.state or "Tamil Nadu",
        "phone": phone,
        "email": order.email or "noreply@sevenxt.com",
        # Append suffix to make unique in Delhivery system
        "order_id": f"{order.order_id}-EXCH-{exchange.id}", 
        "payment_status": "Prepaid", # Exchange replacements are usually prepaid/already paid
        "amount": 0, # No charge for replacement usually, or set to value for insurance
        "length": float(order.length) if order.length else 10.0,
        "breadth": float(order.breadth) if order.breadth else 10.0,
        "height": float(order.height) if order.height else 10.0,
        "weight": float(order.weight) if order.weight else 0.5,
        "item_name": f"Replacement: {exchange.product_name}",
        "quantity": exchange.quantity,
        "service_type": "E",
    }
    
    client = delhivery_client
    
    try:
        response = client.create_shipment(order_data)
        logger.info(f"[EXCHANGE] Forward API Response: {response}")
        
        if not response or "packages" not in response:
            return (None, None)
            
        package = response["packages"][0]
        new_awb = package.get("waybill")
        
        if not new_awb:
            logger.error(f"[EXCHANGE] No waybill for forward shipment")
            return (None, None)
            
        # Fetch Label
        new_label_path = None
        try:
            pdf_content, error = client.fetch_awb_label(new_awb)
            if pdf_content:
                import os
                upload_dir = os.path.join("uploads", "awb")
                os.makedirs(upload_dir, exist_ok=True)
                filename = f"exchange_new_{new_awb}.pdf"
                file_path = os.path.join(upload_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(pdf_content)
                new_label_path = f"/uploads/awb/{filename}"
        except Exception as e:
            logger.exception(f"[EXCHANGE] Error fetching label: {e}")
            
        # Update Order Table (Overwrite old AWB)
        order.awb_number = new_awb
        # We don't change order status to 'AWB_GENERATED' because it might confuse the main flow, 
        # or we might want to set it to 'Exchange Shipped'. 
        # For now, let's keep order status as is or update if needed.
        
        db.commit()
        
        return (new_awb, new_label_path)
        
    except Exception as e:
        logger.exception(f"[EXCHANGE] Failed to create forward shipment: {e}")
        return (None, None)
