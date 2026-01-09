# SendGrid Email Utility for sending OTP emails
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class SendGridService:
    def __init__(self):
        self.client = None
        self.from_email = settings.SENDGRID_FROM_EMAIL
        self.from_name = settings.SENDGRID_FROM_NAME
        
        if settings.SENDGRID_API_KEY:
            try:
                self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)
                logger.info("")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid Client: {e}")

    def send_otp_email(self, to_email: str, otp: str) -> bool:
        """Send OTP via SendGrid"""
        if not self.client:
            logger.warning("SendGrid Client not initialized. Cannot send OTP.")
            print(f"⚠️ SendGrid not configured. OTP for {to_email}: {otp}")
            return False
            
        try:
            # Simplified HTML to improve deliverability
            html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <h2>Password Reset Request</h2>
                <p>Your OTP code is:</p>
                <h1 style="color: #4F46E5; font-size: 32px; letter-spacing: 5px;">{otp}</h1>
                <p>This code is valid for 10 minutes.</p>
                <p style="font-size: 12px; color: #666;">If you did not request this, please ignore this email.</p>
            </div>
            """
            
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject="Your SevenNXT Password Reset Code", # Simpler subject
                html_content=html_content
            )
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"OTP email sent successfully to {to_email}")
                print(f"✅ OTP email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"SendGrid returned status {response.status_code}")
                print(f"❌ SendGrid returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending OTP email via SendGrid: {e}")
            print(f"❌ Error sending OTP email: {e}")
            # Print OTP to console for debugging
            print(f"🔐 OTP for {to_email}: {otp}")
            return False

    def send_exchange_rejection_email(self, to_email: str, customer_name: str, order_id: str, product_name: str, rejection_reason: str) -> bool:
        """Send exchange rejection notification via SendGrid"""
        if not self.client:
            logger.warning("SendGrid Client not initialized. Cannot send rejection email.")
            print(f"⚠️ SendGrid not configured. Rejection email for {to_email}")
            return False
            
        try:
            html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; color: #333; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
                    <h2 style="color: white; margin: 0;">Exchange Request Update</h2>
                </div>
                <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e5e7eb;">
                    <p style="font-size: 16px; margin-bottom: 20px;">Dear {customer_name},</p>
                    
                    <p style="font-size: 14px; line-height: 1.6; color: #555;">
                        We regret to inform you that your exchange request for <strong>{product_name}</strong> 
                        (Order ID: <strong>{order_id}</strong>) has been <span style="color: #dc2626; font-weight: bold;">rejected</span>.
                    </p>
                    
                    <div style="background: #fee2e2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <p style="margin: 0; font-weight: bold; color: #991b1b; font-size: 14px;">Reason for Rejection:</p>
                        <p style="margin: 10px 0 0 0; color: #7f1d1d; font-size: 14px;">{rejection_reason}</p>
                    </div>
                    
                    <p style="font-size: 14px; line-height: 1.6; color: #555;">
                        If you have any questions or concerns about this decision, please don't hesitate to contact our customer support team.
                    </p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                        <p style="font-size: 12px; color: #6b7280; margin: 0;">
                            Thank you for your understanding.<br>
                            <strong>SevenNXT Team</strong>
                        </p>
                    </div>
                </div>
            </div>
            """
            
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=f"Exchange Request Rejected - Order {order_id}",
                html_content=html_content
            )
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Exchange rejection email sent successfully to {to_email}")
                print(f"✅ Exchange rejection email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"SendGrid returned status {response.status_code}")
                print(f"❌ SendGrid returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending exchange rejection email via SendGrid: {e}")
            print(f"❌ Error sending exchange rejection email: {e}")
            return False



    def send_refund_rejection_email(self, to_email: str, customer_name: str, order_id: str, amount: float, rejection_reason: str) -> bool:
        """Send refund rejection notification via SendGrid"""
        if not self.client:
            logger.warning("SendGrid Client not initialized. Cannot send rejection email.")
            return False
            
        try:
            html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; color: #333; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #FF6B6B 0%, #EE5253 100%); padding: 30px; border-radius: 10px 10px 0 0;">
                    <h2 style="color: white; margin: 0;">Refund Request Update</h2>
                </div>
                <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e5e7eb;">
                    <p style="font-size: 16px; margin-bottom: 20px;">Dear {customer_name},</p>
                    
                    <p style="font-size: 14px; line-height: 1.6; color: #555;">
                        We regret to inform you that your refund request for Order ID: <strong>{order_id}</strong> 
                        (Amount: <strong>₹{amount}</strong>) has been <span style="color: #dc2626; font-weight: bold;">rejected</span>.
                    </p>
                    
                    <div style="background: #fee2e2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <p style="margin: 0; font-weight: bold; color: #991b1b; font-size: 14px;">Reason for Rejection:</p>
                        <p style="margin: 10px 0 0 0; color: #7f1d1d; font-size: 14px;">{rejection_reason}</p>
                    </div>
                    
                    <p style="font-size: 14px; line-height: 1.6; color: #555;">
                        If you have any questions or concerns about this decision, please don't hesitate to contact our customer support team.
                    </p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                        <p style="font-size: 12px; color: #6b7280; margin: 0;">
                            Thank you for your understanding.<br>
                            <strong>SevenNXT Team</strong>
                        </p>
                    </div>
                </div>
            </div>
            """
            
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=f"Refund Request Rejected - Order {order_id}",
                html_content=html_content
            )
            
            self.client.send(message)
            logger.info(f"Refund rejection email sent successfully to {to_email}")
            return True
                
        except Exception as e:
            logger.error(f"Error sending refund rejection email: {e}")
            return False

    def send_refund_approval_email(self, to_email: str, customer_name: str, order_id: str, amount: float) -> bool:
        """Send refund approval notification via SendGrid"""
        if not self.client:
            logger.warning("SendGrid Client not initialized. Cannot send approval email.")
            return False
            
        try:
            html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; color: #333; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); padding: 30px; border-radius: 10px 10px 0 0;">
                    <h2 style="color: white; margin: 0;">Refund Request Approved</h2>
                </div>
                <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e5e7eb;">
                    <p style="font-size: 16px; margin-bottom: 20px;">Dear {customer_name},</p>
                    
                    <p style="font-size: 14px; line-height: 1.6; color: #555;">
                        Good news! Your refund request for Order ID: <strong>{order_id}</strong> 
                        (Amount: <strong>₹{amount}</strong>) has been <span style="color: #059669; font-weight: bold;">approved</span>.
                    </p>
                    
                    <div style="background: #ecfdf5; border-left: 4px solid #059669; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <p style="margin: 0; font-weight: bold; color: #064e3b; font-size: 14px;">Next Steps:</p>
                        <p style="margin: 10px 0 0 0; color: #065f46; font-size: 14px;">
                        1. A separate email with your return shipping label has been sent.<br>
                        2. Please pack the item securely.<br>
                        3. Our delivery partner will pick up the package soon.
                        </p>
                    </div>
                    
                    <p style="font-size: 14px; line-height: 1.6; color: #555;">
                        Once we receive and verify the item, the refund amount will be credited to your original payment method.
                    </p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                        <p style="font-size: 12px; color: #6b7280; margin: 0;">
                            Thank you for shopping with us.<br>
                            <strong>SevenNXT Team</strong>
                        </p>
                    </div>
                </div>
            </div>
            """
            
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=f"Refund Request Approved - Order {order_id}",
                html_content=html_content
            )
            
            self.client.send(message)
            logger.info(f"Refund approval email sent successfully to {to_email}")
            return True
                
        except Exception as e:
            logger.error(f"Error sending refund approval email: {e}")
            return False

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Generic email sender via SendGrid"""
        if not self.client:
            logger.warning("SendGrid Client not initialized.")
            print(f"⚠️ SendGrid not configured. Email to {to_email}")
            return False
            
        try:
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            response = self.client.send(message)
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                print(f"✅ Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"SendGrid returned status {response.status_code}")
                print(f"❌ SendGrid error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            print(f"❌ Error sending email: {e}")
            return False


sendgrid_service = SendGridService()


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Standalone wrapper for sending emails"""
    return sendgrid_service.send_email(to_email, subject, html_content)
