from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.modules.exchanges import service as exchange_service
from app.modules.delivery.delhivery_client import delhivery_client
from app.modules.orders.service import get_order_by_id, update_order_awb
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exchanges", tags=["Exchange Webhooks"])


@router.post("/{exchange_id}/generate-return-awb")
async def generate_return_awb(
    exchange_id: str,
    db: Session = Depends(get_db)
):
    """
    Generate return AWB for customer to send back old product
    """
    try:
        exchange = exchange_service.get_exchange_by_id(db, exchange_id)
        if not exchange:
            raise HTTPException(status_code=404, detail="Exchange not found")
        
        # Get order details
        order = get_order_by_id(db, exchange.order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Create return shipment data
        shipment_data = {
            "name": exchange.customer_name,
            "add": order.address,
            "phone": exchange.customer_phone,
            "pin": order.pincode,
            "city": order.city,
            "state": order.state,
            "payment_mode": "Prepaid",  # Return is always prepaid
            "return_add": "Your Warehouse Address",  # TODO: Get from config
            "return_pin": "600018",  # TODO: Get from config
            "return_phone": "1234567890",  # TODO: Get from config
            "return_name": "SevenXT",
            "order": f"{exchange_id}-RETURN",
            "products_desc": f"Return: {exchange.original_product_name}",
            "hsn_code": "HSN123",  # TODO: Get from product
            "cod_amount": "0",
            "weight": "500",  # TODO: Get from product
            "seller_name": "SevenXT"
        }
        
        # Call Delhivery API to create return shipment
        result = delhivery_client.create_shipment(shipment_data)
        
        if result.get("success"):
            awb_number = result.get("awb_number")
            label_path = result.get("label_path")
            
            # Update exchange with return AWB
            exchange_service.update_return_awb(db, exchange_id, awb_number, label_path)
            
            # TODO: Send email to customer with return label
            
            logger.info(f"Generated return AWB {awb_number} for exchange {exchange_id}")
            
            return {
                "success": True,
                "awb_number": awb_number,
                "label_path": label_path,
                "message": "Return AWB generated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate return AWB")
            
    except Exception as e:
        logger.exception(f"Error generating return AWB for exchange {exchange_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{exchange_id}/generate-new-product-awb")
async def generate_new_product_awb(
    exchange_id: str,
    db: Session = Depends(get_db)
):
    """
    Generate forward AWB to send new product to customer
    Only after quality check passes
    """
    try:
        exchange = exchange_service.get_exchange_by_id(db, exchange_id)
        if not exchange:
            raise HTTPException(status_code=404, detail="Exchange not found")
        
        # Check if quality approved
        if not exchange.quality_approved:
            raise HTTPException(status_code=400, detail="Quality check not approved")
        
        # Get order details
        order = get_order_by_id(db, exchange.order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Calculate COD amount if price difference
        cod_amount = "0"
        payment_mode = "Prepaid"
        if exchange.price_difference and exchange.price_difference > 0:
            cod_amount = str(exchange.price_difference)
            payment_mode = "COD"
        
        # Create forward shipment data
        shipment_data = {
            "name": exchange.customer_name,
            "add": order.address,
            "phone": exchange.customer_phone,
            "pin": order.pincode,
            "city": order.city,
            "state": order.state,
            "payment_mode": payment_mode,
            "order": f"{exchange_id}-FORWARD",
            "products_desc": f"Exchange: {exchange.exchange_product_name}",
            "hsn_code": "HSN456",  # TODO: Get from product
            "cod_amount": cod_amount,
            "weight": "500",  # TODO: Get from product
            "seller_name": "SevenXT"
        }
        
        # Call Delhivery API to create forward shipment
        result = delhivery_client.create_shipment(shipment_data)
        
        if result.get("success"):
            awb_number = result.get("awb_number")
            label_path = result.get("label_path")
            
            # Update exchange with new product AWB
            exchange_service.update_new_product_awb(db, exchange_id, awb_number, label_path)
            
            # Update order with new AWB (replace old AWB)
            update_order_awb(db, order.order_id, awb_number, label_path)
            
            logger.info(f"Generated new product AWB {awb_number} for exchange {exchange_id}")
            
            return {
                "success": True,
                "awb_number": awb_number,
                "label_path": label_path,
                "message": "New product AWB generated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate new product AWB")
            
    except Exception as e:
        logger.exception(f"Error generating new product AWB for exchange {exchange_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/delhivery")
async def delhivery_webhook(
    webhook_data: dict,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle Delhivery webhook updates for BOTH exchange and refund shipments
    Accepts both 'awb' and 'waybill' as AWB number field
    
    This webhook is called by Delhivery when delivery status changes:
    - Picked Up
    - In Transit
    - Out For Delivery
    - Delivered
    - Failed Attempt
    - RTO (Return to Origin)
    """
    try:
        # Support both 'awb' and 'waybill' field names
        awb_number = webhook_data.get("awb") or webhook_data.get("waybill")
        status = webhook_data.get("status")
        
        # If status not in root, check scans array (Delhivery's actual format)
        if not status and "scans" in webhook_data:
            scans = webhook_data.get("scans", [])
            if scans and len(scans) > 0:
                # Get the latest scan
                latest_scan = scans[-1]
                scan_detail = latest_scan.get("ScanDetail", {})
                # Try different field names
                status = (scan_detail.get("Scan") or 
                         scan_detail.get("Status") or 
                         scan_detail.get("ScanType"))
                logger.info(f"[WEBHOOK] Extracted status from scans array: {status}")
        
        if not awb_number or not status:
            logger.warning(f"Missing AWB or status in webhook data: {webhook_data}")
            return {"success": False, "error": "Missing AWB number or status"}
        
        logger.info(f"[WEBHOOK] Received update for AWB: {awb_number}, Status: {status}")
        
        # ============================================
        # CHECK BOTH EXCHANGES AND REFUNDS
        # ============================================
        
        # 1. Check if this AWB belongs to an EXCHANGE
        from app.modules.exchanges.models import Exchange
        exchanges = db.query(Exchange).filter(
            (Exchange.return_awb_number == awb_number) |
            (Exchange.new_awb_number == awb_number)
        ).all()
        
        # 2. Check if this AWB belongs to a REFUND
        from app.modules.refunds.models import Refund
        refunds = db.query(Refund).filter(
            Refund.return_awb_number == awb_number
        ).all()
        
        # If neither found, return error
        if not exchanges and not refunds:
            logger.warning(f"[WEBHOOK] No exchange or refund found for AWB: {awb_number}")
            return {"success": False, "error": f"No exchange or refund found for AWB {awb_number}"}
        
        for exchange in exchanges:
            if exchange.return_awb_number == awb_number:
                # Update return delivery status
                logger.info(f"[WEBHOOK] Updating return delivery status for exchange {exchange.id}: {status}")
                exchange.return_delivery_status = status
                
                # Normalize status for comparison
                status_lower = status.lower().replace(" ", "").replace("_", "")
                
                # Update overall exchange status based on delivery status
                if status_lower in ["delivered", "delivery", "dlvd"]:
                    exchange.status = "Return Received"
                    # Update parent order status
                    if exchange.order:
                        exchange.order.status = "Return Received"
                        exchange.order.updated_at = datetime.utcnow()
                        logger.info(f"[WEBHOOK] Order {exchange.order.order_id} status updated to 'Return Received'")
                    logger.info(f"[WEBHOOK] Exchange {exchange.id} status updated to 'Return Received'")
                    
                elif status_lower in ["pickedup", "pickup", "manifested", "manifest"]:
                    if exchange.status == "Approved":
                        exchange.status = "Return In Transit"
                        # Update parent order status
                        if exchange.order:
                            exchange.order.status = "Return In Transit"
                            exchange.order.updated_at = datetime.utcnow()
                            logger.info(f"[WEBHOOK] Order {exchange.order.order_id} status updated to 'Return In Transit'")
                        logger.info(f"[WEBHOOK] Exchange {exchange.id} status updated to 'Return In Transit'")
                        
                elif status_lower in ["intransit", "transit", "outfordelivery", "dispatched"]:
                    # Keep as Return In Transit
                    if exchange.order:
                        exchange.order.status = "Return In Transit"
                        exchange.order.updated_at = datetime.utcnow()
                
                # FAILED DELIVERY HANDLING
                elif status_lower in ["attemptfail", "failed", "failedattempt", "undelivered", "notdelivered"]:
                    # Delivery attempt failed - increment counter
                    print(f"\n{'='*60}")
                    print(f"🔍 DEBUG: Failed delivery detected for AWB {awb_number}")
                    print(f"   Exchange ID: {exchange.id}")
                    print(f"   Current delivery_attempts: {exchange.delivery_attempts}")
                    
                    if not hasattr(exchange, 'delivery_attempts') or exchange.delivery_attempts is None:
                        exchange.delivery_attempts = 0
                        print(f"   ⚠️  Initialized delivery_attempts to 0")
                    
                    exchange.delivery_attempts += 1
                    print(f"   ✅ Incremented to: {exchange.delivery_attempts}")
                    
                    logger.warning(f"[WEBHOOK] ⚠️ Return delivery attempt {exchange.delivery_attempts} failed for exchange {exchange.id}: {status}")
                    
                    # Keep status as is, just update delivery_status field
                    # Don't change main exchange status
                    
                    # Alert if too many attempts
                    if exchange.delivery_attempts >= 3:
                        print(f"\n🚨 CRITICAL THRESHOLD REACHED!")
                        print(f"   Attempts: {exchange.delivery_attempts} >= 3")
                        print(f"   Triggering email alert...")
                        
                        logger.error(f"[WEBHOOK] 🚨 CRITICAL: Return delivery failed {exchange.delivery_attempts} times for exchange {exchange.id}")
                        
                        # Send alert email to admin
                        try:
                            print(f"   📧 Importing send_email function...")
                            from app.modules.auth.sendgrid_utils import send_email
                            print(f"   ✅ Import successful")
                            
                            admin_email = "loguloges77@gmail.com"  # Your admin email
                            subject = f"🚨 CRITICAL: Delivery Failed 3 Times - Exchange #{exchange.id}"
                            
                            print(f"   📧 Preparing email...")
                            print(f"      To: {admin_email}")
                            print(f"      Subject: {subject}")
                            
                            html_content = f"""
                            <html>
                                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #FEF2F2; border: 2px solid #DC2626; border-radius: 8px;">
                                        <h2 style="color: #DC2626; margin-top: 0;">🚨 CRITICAL ALERT: Delivery Failed Multiple Times</h2>
                                        
                                        <div style="background-color: white; padding: 15px; border-radius: 8px; margin: 20px 0;">
                                            <h3 style="margin-top: 0;">Exchange Details:</h3>
                                            <p><strong>Exchange ID:</strong> {exchange.id}</p>
                                            <p><strong>Order ID:</strong> {exchange.order.order_id if exchange.order else 'N/A'}</p>
                                            <p><strong>Customer:</strong> {exchange.order.customer_name if exchange.order else 'N/A'}</p>
                                            <p><strong>AWB Number:</strong> {awb_number}</p>
                                            <p><strong>Failed Attempts:</strong> {exchange.delivery_attempts}</p>
                                            <p><strong>Last Status:</strong> {status}</p>
                                        </div>
                                        
                                        <div style="background-color: #FEF2F2; padding: 15px; border-left: 4px solid #DC2626; margin: 20px 0;">
                                            <h3 style="margin-top: 0; color: #DC2626;">⚠️ Action Required:</h3>
                                            <ul>
                                                <li>Contact the customer immediately</li>
                                                <li>Verify the delivery address</li>
                                                <li>Check if customer is available</li>
                                                <li>Consider manual intervention or refund</li>
                                            </ul>
                                        </div>
                                        
                                        <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #E5E7EB;">
                                            <strong>Need Help?</strong><br>
                                            Check the admin dashboard for more details.
                                        </p>
                                    </div>
                                </body>
                            </html>
                            """
                            
                            print(f"   📤 Calling send_email()...")
                            result = send_email(
                                to_email=admin_email,
                                subject=subject,
                                html_content=html_content
                            )
                            
                            if result:
                                print(f"   ✅ send_email() returned True - EMAIL SENT!")
                                logger.info(f"[WEBHOOK] ✅ Alert email sent to admin for exchange {exchange.id}")
                            else:
                                print(f"   ❌ send_email() returned False - EMAIL FAILED!")
                                logger.error(f"[WEBHOOK] ❌ send_email returned False")
                            
                            print(f"{'='*60}\n")
                            
                        except Exception as email_error:
                            print(f"   ❌ EXCEPTION: {email_error}")
                            print(f"{'='*60}\n")
                            logger.error(f"[WEBHOOK] ❌ Failed to send alert email: {email_error}")
                    else:
                        print(f"   ℹ️  Not enough attempts yet ({exchange.delivery_attempts}/3)")
                        print(f"{'='*60}\n")


                
                # EXCEPTION HANDLING
                elif status_lower in ["exception", "rto", "returntosender", "lost", "damaged", "cancelled"]:
                    # Critical issue - needs admin attention
                    logger.error(f"[WEBHOOK] 🚨 CRITICAL: Exception in return delivery for exchange {exchange.id}: {status}")
                    exchange.return_delivery_status = f"EXCEPTION: {status}"
                    
                    # Don't auto-update main status, let admin handle
                    # Mark for manual review
                    if status_lower in ["rto", "returntosender"]:
                        logger.error(f"[WEBHOOK] Return shipment RTO (Return to Sender) for exchange {exchange.id}")
                        # TODO: Notify admin immediately
                    elif status_lower in ["lost", "damaged"]:
                        logger.error(f"[WEBHOOK] Return shipment {status} for exchange {exchange.id}")
                        # TODO: Initiate insurance claim process
                    

                    
            elif exchange.new_awb_number == awb_number:
                # Update new product delivery status
                logger.info(f"[WEBHOOK] Updating new delivery status for exchange {exchange.id}: {status}")
                exchange.new_delivery_status = status
                
                # Normalize status
                status_lower = status.lower().replace(" ", "").replace("_", "")
                
                # Update overall exchange status based on delivery status
                if status_lower in ["delivered", "delivery", "dlvd"]:
                    exchange.status = "Completed"
                    exchange.completed_at = datetime.utcnow()
                    # Update parent order status to Delivered
                    if exchange.order:
                        exchange.order.status = "Delivered"
                        exchange.order.updated_at = datetime.utcnow()
                        logger.info(f"[WEBHOOK] Order {exchange.order.order_id} status updated to 'Delivered'")
                    logger.info(f"[WEBHOOK] Exchange {exchange.id} completed")
                    
                elif status_lower in ["intransit", "transit", "outfordelivery", "dispatched", "pickedup"]:
                    # Update order status to match
                    if exchange.order:
                        exchange.order.status = "In Transit"
                        exchange.order.updated_at = datetime.utcnow()
                        logger.info(f"[WEBHOOK] Order {exchange.order.order_id} status updated to 'In Transit'")
                
                # FAILED DELIVERY HANDLING FOR NEW PRODUCT
                elif status_lower in ["attemptfail", "failed", "failedattempt", "undelivered", "notdelivered"]:
                    # New product delivery attempt failed
                    if not hasattr(exchange, 'new_delivery_attempts') or exchange.new_delivery_attempts is None:
                        exchange.new_delivery_attempts = 0
                    exchange.new_delivery_attempts += 1
                    
                    logger.warning(f"[WEBHOOK] ⚠️ New product delivery attempt {exchange.new_delivery_attempts} failed for exchange {exchange.id}: {status}")
                    
                    # Alert if too many attempts
                    if exchange.new_delivery_attempts >= 3:
                        logger.error(f"[WEBHOOK] 🚨 CRITICAL: New product delivery failed {exchange.new_delivery_attempts} times for exchange {exchange.id}")
                        # TODO: Send alert email to admin and customer
                        # TODO: Consider refund or re-attempt
                
                # EXCEPTION HANDLING FOR NEW PRODUCT
                elif status_lower in ["exception", "rto", "returntosender", "lost", "damaged", "cancelled"]:
                    logger.error(f"[WEBHOOK] 🚨 CRITICAL: Exception in new product delivery for exchange {exchange.id}: {status}")
                    exchange.new_delivery_status = f"EXCEPTION: {status}"
                    
                    if status_lower in ["rto", "returntosender"]:
                        logger.error(f"[WEBHOOK] New product RTO for exchange {exchange.id} - Customer refused or unavailable")
                        # TODO: Contact customer, reschedule, or process refund
                    elif status_lower in ["lost", "damaged"]:
                        logger.error(f"[WEBHOOK] New product {status} for exchange {exchange.id}")
                        # TODO: Initiate insurance claim, send replacement

        
        # ============================================
        # PROCESS REFUNDS
        # ============================================
        for refund in refunds:
            logger.info(f"[WEBHOOK] Processing refund {refund.id} for AWB: {awb_number}")
            
            # Update return delivery status
            refund.return_delivery_status = status
            
            # Normalize status for comparison
            status_lower = status.lower().replace(" ", "").replace("_", "")
            
            # Update refund status based on delivery status
            if status_lower in ["delivered", "delivery", "dlvd"]:
                # Return product delivered to warehouse
                refund.status = "Return Received"
                
                # Update parent order status
                if refund.order:
                    refund.order.status = "Return Received"
                    refund.order.updated_at = datetime.utcnow()
                    logger.info(f"[WEBHOOK] Order {refund.order.order_id} status updated to 'Return Received'")
                
                logger.info(f"[WEBHOOK] Refund {refund.id} status updated to 'Return Received'")
                
            elif status_lower in ["pickedup", "pickup", "manifested", "manifest"]:
                # Product picked up from customer
                if refund.status == "Approved":
                    refund.status = "Return In Transit"
                    
                    # Update parent order status
                    if refund.order:
                        refund.order.status = "Return In Transit"
                        refund.order.updated_at = datetime.utcnow()
                        logger.info(f"[WEBHOOK] Order {refund.order.order_id} status updated to 'Return In Transit'")
                    
                    logger.info(f"[WEBHOOK] Refund {refund.id} status updated to 'Return In Transit'")
                    
            elif status_lower in ["intransit", "transit", "outfordelivery", "dispatched"]:
                # Keep as Return In Transit
                if refund.order:
                    refund.order.status = "Return In Transit"
                    refund.order.updated_at = datetime.utcnow()
            
            # FAILED DELIVERY HANDLING
            elif status_lower in ["attemptfail", "failed", "failedattempt", "undelivered", "notdelivered"]:
                logger.warning(f"[WEBHOOK] ⚠️ Return delivery attempt failed for refund {refund.id}: {status}")
                
                # Send alert email to admin
                try:
                    from app.modules.auth.sendgrid_utils import send_email
                    
                    admin_email = "loguloges77@gmail.com"  # Your admin email
                    subject = f"🚨 Refund Return Delivery Failed - Refund #{refund.id}"
                    
                    html_content = f"""
                    <html>
                        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #FEF2F2; border: 2px solid #DC2626; border-radius: 8px;">
                                <h2 style="color: #DC2626; margin-top: 0;">🚨 Refund Return Delivery Failed</h2>
                                
                                <div style="background-color: white; padding: 15px; border-radius: 8px; margin: 20px 0;">
                                    <h3 style="margin-top: 0;">Refund Details:</h3>
                                    <p><strong>Refund ID:</strong> {refund.id}</p>
                                    <p><strong>Order ID:</strong> {refund.order.order_id if refund.order else 'N/A'}</p>
                                    <p><strong>Customer:</strong> {refund.order.customer_name if refund.order else 'N/A'}</p>
                                    <p><strong>AWB Number:</strong> {awb_number}</p>
                                    <p><strong>Status:</strong> {status}</p>
                                    <p><strong>Reason:</strong> {refund.reason}</p>
                                </div>
                                
                                <div style="background-color: #FEF2F2; padding: 15px; border-left: 4px solid #DC2626; margin: 20px 0;">
                                    <h3 style="margin-top: 0; color: #DC2626;">⚠️ Action Required:</h3>
                                    <ul>
                                        <li>Contact the customer immediately</li>
                                        <li>Verify the pickup address</li>
                                        <li>Check if customer is available</li>
                                        <li>Reschedule pickup or arrange alternative</li>
                                    </ul>
                                </div>
                                
                                <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #E5E7EB;">
                                    <strong>Need Help?</strong><br>
                                    Check the admin dashboard for more details.
                                </p>
                            </div>
                        </body>
                    </html>
                    """
                    
                    send_email(
                        to_email=admin_email,
                        subject=subject,
                        html_content=html_content
                    )
                    logger.info(f"[WEBHOOK] ✅ Alert email sent to admin for refund {refund.id}")
                    
                except Exception as email_error:
                    logger.error(f"[WEBHOOK] ❌ Failed to send alert email: {email_error}")
            
            # EXCEPTION HANDLING
            elif status_lower in ["exception", "rto", "returntosender", "lost", "damaged", "cancelled"]:
                logger.error(f"[WEBHOOK] 🚨 CRITICAL: Exception in refund return delivery for refund {refund.id}: {status}")
                refund.return_delivery_status = f"EXCEPTION: {status}"
                
                if status_lower in ["rto", "returntosender"]:
                    logger.error(f"[WEBHOOK] Refund return shipment RTO (Return to Sender) for refund {refund.id}")
                    # TODO: Notify admin immediately
                elif status_lower in ["lost", "damaged"]:
                    logger.error(f"[WEBHOOK] Refund return shipment {status} for refund {refund.id}")
                    # TODO: Initiate insurance claim process

        
        db.commit()
        logger.info(f"[WEBHOOK] Successfully processed webhook for AWB: {awb_number}")
        
        return {
            "success": True, 
            "message": "Webhook processed successfully",
            "awb": awb_number,
            "status": status,
            "exchanges_updated": len(exchanges),
            "refunds_updated": len(refunds)
        }
        
    except Exception as e:
        logger.exception(f"[WEBHOOK] Error processing Delhivery webhook: {e}")
        return {"success": False, "error": str(e)}

