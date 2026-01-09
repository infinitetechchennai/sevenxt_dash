from typing import Optional
from sqlalchemy.orm import Session
from app.modules.orders.models import Order, Delivery
from app.modules.delivery.delhivery_client import DelhiveryClient
import logging
import re

logger = logging.getLogger(__name__)

DELHIVERY_TOKEN = "cb5e84d71ecff61c73abc80b20b326dec8302d8c"


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
        
   
    # 1. Check if AWB already exists
    if order.awb_number:
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
    # Resolve customer name
    # Resolve customer name
    customer_name = order.customer_name or "Customer"

    # Use separate city, state, pincode fields (no parsing from address)
    city = order.city if (hasattr(order, 'city') and order.city) else "Chennai"
    state = order.state if (hasattr(order, 'state') and order.state) else "Tamil Nadu"
    pincode = order.pincode if (hasattr(order, 'pincode') and order.pincode) else "600001"

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
    }

    logger.info(f"[SHIPMENT] Payload prepared: {order_data}")

    # 5. Call Delhivery API
    client = DelhiveryClient(token=DELHIVERY_TOKEN, is_production=False)
    
    try:
        # Force update warehouse details to ensure correct address on label
        logger.info("[SHIPMENT] Updating warehouse details...")
        try:
            client.create_warehouse()
        except Exception as wh_e:
            logger.warning(f"[SHIPMENT] Warehouse update failed (non-fatal): {wh_e}")

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
    client = DelhiveryClient(token=DELHIVERY_TOKEN, is_production=False)
    
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
                
                # Send email with AWB label
                send_return_label_email(order.email, order.customer_name, return_awb, file_path, refund.reason)
            else:
                logger.error(f"[RETURN] Failed to fetch return label after all retries")
        
        except Exception as e:
            logger.exception(f"[RETURN] Error fetching/saving label: {e}")
        
        return (return_awb, return_label_path)
    
    except Exception as e:
        logger.exception(f"[RETURN] Failed to create return shipment: {e}")
        return (None, None)


def send_return_label_email(customer_email: str, customer_name: str, awb_number: str, label_path: str, reason: str):
    """
    Send return AWB label to customer via SendGrid
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
            return
        
        # Check if file exists
        if not os.path.exists(label_path):
            logger.error(f"[EMAIL] Label file not found: {label_path}")
            return
        
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
        
        logger.info(f"[EMAIL] Attachment created successfully")
        
        # Create email with proper from format
        message = Mail(
            from_email=From(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
            to_emails=customer_email,
            subject=f'Return Label for Your Refund Request - AWB: {awb_number}',
            html_content=f'''
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
        )
        
        message.attachment = attached_file
        
        logger.info(f"[EMAIL] Email message created, sending via SendGrid...")
        
        # Send email
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"[EMAIL] ✅ Return label sent successfully to {customer_email}. Status: {response.status_code}")
        logger.info(f"[EMAIL] Response headers: {response.headers}")
        
        return True
        
    except FileNotFoundError as e:
        logger.error(f"[EMAIL] ❌ Label file not found: {e}")
        return False
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
    
    client = DelhiveryClient(token=DELHIVERY_TOKEN, is_production=False)
    
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
    
    client = DelhiveryClient(token=DELHIVERY_TOKEN, is_production=False)
    
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
