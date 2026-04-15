from sqlalchemy.orm import Session
from . import models
from app.config import settings
from twilio.rest import Client

def get_b2b_users(db: Session):
    return db.query(models.B2BApplication).all()

def update_status(db: Session, user_id: int, new_status: str):
    user = db.query(models.B2BApplication).filter(models.B2BApplication.id == user_id).first()
    
    if user:
        # If the user is already rejected, we can add a check here if you want to block it at DB level too
        # if user.status == 'rejected': return user 

        allowed_statuses = ['approved', 'pending_approval', 'suspended', 'rejected']
        if new_status in allowed_statuses:
            user.status = new_status
            db.commit()
            db.refresh(user)

            # SMS Logic
            if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
                try:
                    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                    messages = {
                        "approved": f"Congratulations {user.bussiness_name}! Your account is Approved.",
                        "rejected": f"Hi {user.bussiness_name}, your B2B application has been Rejected.",
                        "suspended": f"Your B2B account for {user.bussiness_name} is suspended.",
                    }
                    msg_body = messages.get(new_status)
                    if msg_body:
                        phone = str(user.phone_number)
                        to_phone = phone if phone.startswith('+') else f"+91{phone}"
                        client.messages.create(body=msg_body, from_=settings.TWILIO_PHONE_NUMBER, to=to_phone)
                except Exception as e:
                    print(f"SMS Error: {e}")
            
            return user
    return None