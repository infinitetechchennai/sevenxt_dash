from sqlalchemy import Column, Integer, String, Text, Enum, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

# --- WORKFLOW: STATIC PAGES ---
class CMSPage(Base):
    __tablename__ = "cms_pages"
    # This allows SQLAlchemy to redefine the table if it was already loaded in memory
    __table_args__ = {'extend_existing': True} 

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum("Published", "Draft", name="page_status"), default="Published")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# --- WORKFLOW: CATEGORY BANNERS ---
class CMSCategoryBanner(Base):
    __tablename__ = "cms_category_banners"

    id = Column(Integer, primary_key=True)
    category = Column(String(100), unique=True, nullable=True) 
    image_url = Column(String(500), nullable=True)             
    status = Column(Boolean, default=True)

# --- WORKFLOW: HOMEPAGE BANNERS ---
class CMSBanner(Base):
    __tablename__ = "cms_banners"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    image = Column(String(500), nullable=False)
    position = Column(String(50), nullable=False)
    status = Column(Enum("Active", "Inactive", name="banner_status"), default="Active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# --- WORKFLOW: NOTIFICATIONS ---
class CMSNotification(Base):
    __tablename__ = "cms_notifications"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    audience = Column(String(100), nullable=False)
    status = Column(Enum("SENT", "FAILED", name="notification_status"), default="SENT")
    created_at = Column(DateTime(timezone=True), server_default=func.now())