from sqlalchemy.orm import Session
from sqlalchemy import text
from .models import CMSBanner, CMSCategoryBanner, CMSNotification, CMSPage, AppNotification
from twilio.rest import Client
from app.config import settings
import logging
from . import models  
# ✅ Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- WORKFLOW 1: HOMEPAGE BANNERS ---
def get_banners(db: Session):
    return db.query(CMSBanner).all()

def create_banner(db: Session, data: dict):
    banner = CMSBanner(**data)
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner

def delete_banner(db: Session, banner_id: int):
    banner = db.query(CMSBanner).filter(CMSBanner.id == banner_id).first()
    if banner:
        db.delete(banner)
        db.commit()
        return True
    return False


# --- Add this function to your service.py ---

def update_banner(db: Session, banner_id: int, banner_data: dict):
    # 1. Find the banner by ID
    db_banner = db.query(models.CMSBanner).filter(models.CMSBanner.id == banner_id).first()
    
    if db_banner:
        # 2. Loop through the new data and update the fields
        for key, value in banner_data.items():
            if hasattr(db_banner, key):
                setattr(db_banner, key, value)
        
        # 3. Save to database
        db.commit()
        db.refresh(db_banner)
        return db_banner
        
    return None

# --- WORKFLOW 2: CATEGORY BANNERS ---
def get_category_banners(db: Session):
    try:
        return db.query(CMSCategoryBanner).all()
    except Exception as e:
        logger.error(f"Error fetching category banners: {e}")
        return []

def update_category_banner(db: Session, category_id: int, data: dict):
    banner = db.query(CMSCategoryBanner).filter(CMSCategoryBanner.id == category_id).first()
    try:
        if banner:
            for k, v in data.items():
                if hasattr(banner, k):
                    setattr(banner, k, v)
        else:
            banner = CMSCategoryBanner(id=category_id, **data)
            db.add(banner)
        
        db.commit()
        db.refresh(banner)
        return banner
    except Exception as e:
        db.rollback() 
        logger.error(f"DB Error in update_category_banner: {e}")
        return None

# --- WORKFLOW 3: NOTIFICATION MANAGER (TWILIO INTEGRATED) ---

def get_notifications(db: Session):
    return db.query(CMSNotification).order_by(CMSNotification.id.desc()).all()

def create_notification(db: Session, data: dict):
    """
    Saves notification history and broadcasts SMS using direct SQL contact
    to b2b_applications and b2c_applications tables.
    """
    # 1. Create history record in MySQL
    new_notif = CMSNotification(
        title=data.get('title'),
        message=data.get('message'),
        audience=data.get('audience'),
        status="SENT"
    )
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)

    audience = data.get('audience')
    phone_numbers = []

    try:
        # 2. Direct Database Contact (Raw SQL to get phone_number column)
        if audience == "All Users":
            b2b = db.execute(text("SELECT phone_number FROM b2b_applications")).fetchall()
            b2c = db.execute(text("SELECT phone_number FROM b2c_applications")).fetchall()
            phone_numbers = [row[0] for row in b2b if row[0]] + [row[0] for row in b2c if row[0]]
        
        elif audience == "B2B Customers Only":
            b2b = db.execute(text("SELECT phone_number FROM b2b_applications")).fetchall()
            phone_numbers = [row[0] for row in b2b if row[0]]
            
        elif audience == "B2C Customers Only":
            b2c = db.execute(text("SELECT phone_number FROM b2c_applications")).fetchall()
            phone_numbers = [row[0] for row in b2c if row[0]]

        # Remove duplicates
        unique_numbers = list(set(phone_numbers))

        # 3. Initialize Twilio from config.py
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        sent_count = 0
        for raw_num in unique_numbers:
            # Clean non-digits
            clean_num = "".join(filter(str.isdigit, str(raw_num)))

            # Format to E.164 (Assuming India +91 if 10 digits)
            if len(clean_num) == 10:
                formatted_num = f"+91{clean_num}"
            elif len(clean_num) == 12 and clean_num.startswith("91"):
                formatted_num = f"+{clean_num}"
            elif str(raw_num).startswith("+"):
                formatted_num = raw_num
            else:
                logger.warning(f"Invalid phone format skipped: {raw_num}")
                continue

            # 4. Attempt SMS Send
            try:
                client.messages.create(
                    body=f"{new_notif.title}\n{new_notif.message}",
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=formatted_num
                )
                sent_count += 1
            except Exception as sms_err:
                logger.error(f"Twilio error for {formatted_num}: {sms_err}")

        logger.info(f"Broadcast complete. SMS sent to {sent_count} users.")
        return new_notif

    except Exception as e:
        db.rollback()
        logger.error(f"Critical Notification Error: {e}")
        new_notif.status = "FAILED"
        db.commit()
        return new_notif

# --- WORKFLOW: APP NOTIFICATIONS ---
def get_app_notifications(db: Session):
    return db.query(AppNotification).order_by(AppNotification.created_at.desc()).all()

def create_app_notification(db: Session, data: dict):
    notif = AppNotification(**data)
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif

# --- WORKFLOW 4: STATIC PAGES ---
def get_pages(db: Session):
    return db.query(CMSPage).all()

def update_page(db: Session, page_id: int, data: dict):
    page = db.query(CMSPage).filter(CMSPage.id == page_id).first()
    try:
        if page:
            for k, v in data.items():
                if hasattr(page, k):
                    setattr(page, k, v)
            db.commit()
            db.refresh(page)
            return page
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating page: {e}")
        return None