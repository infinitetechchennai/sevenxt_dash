from sqlalchemy.orm import Session
from . import models
from app.config import settings
from twilio.rest import Client

def get_b2b_users(db: Session):
    return db.query(models.B2BApplication).all()

def update_status(db: Session, user_id, new_status: str):
    user = db.query(models.B2BApplication).filter(models.B2BApplication.id == str(user_id)).first()
    
    if user:
        # If the user is already rejected, we can add a check here if you want to block it at DB level too
        # if user.status == 'rejected': return user 

        allowed_statuses = ['approved', 'pending_approval', 'suspended', 'rejected']
        status_clean = (new_status or "").strip().lower()
        if status_clean in allowed_statuses:
            user.status = status_clean
            db.commit()
            db.refresh(user)

            # SMS Logic
            if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
                try:
                    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                    display_name = getattr(user, 'bussiness_name', None) or getattr(user, 'business_name', None) or "Partner"
                    messages = {
                        "approved": f"Congratulations {display_name}! Your account is Approved.",
                        "rejected": f"Hi {display_name}, your B2B application has been Rejected.",
                        "suspended": f"Your B2B account for {display_name} is suspended.",
                    }
                    msg_body = messages.get(status_clean)
                    if msg_body and user.phone_number:
                        phone = str(user.phone_number).strip()
                        to_phone = phone if phone.startswith('+') else f"+91{phone}"
                        client.messages.create(body=msg_body, from_=settings.TWILIO_PHONE_NUMBER, to=to_phone)
                except Exception as e:
                    print(f"SMS Error: {e}")
            
            return user
    return None