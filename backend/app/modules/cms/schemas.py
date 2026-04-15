from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

# --- 1. HOMEPAGE BANNERS ---
class BannerBase(BaseModel):
    title: str
    image: str
    position: str
    status: str

class BannerCreate(BannerBase):
    pass

class BannerResponse(BannerBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

    @field_validator('image')
    @classmethod
    def force_https_image(cls, v: str | None) -> str | None:
        if v and v.startswith("http://"):
            return v.replace("http://", "https://")
        return v

# --- 2. CATEGORY BANNERS ---
class CategoryBannerResponse(BaseModel):
    id: int
    category: Optional[str] = None
    image_url: Optional[str] = None  # Crucial for handling NULLs
    status: bool
    class Config:
        from_attributes = True

    @field_validator('image_url')
    @classmethod
    def force_https_image_url(cls, v: str | None) -> str | None:
        if v and v.startswith("http://"):
            return v.replace("http://", "https://")
        return v

# --- 3. NOTIFICATIONS ---
class NotificationCreate(BaseModel):
    title: str
    message: str
    audience: str

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    audience: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- 4. APP NOTIFICATIONS ---
class AppNotificationCreate(BaseModel):
    title: str
    message: str
    audience: str # 'all', 'b2b', 'b2c'

class AppNotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    audience: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- 5. STATIC PAGES ---
class PageUpdate(BaseModel):
    title: str
    content: str

class PageResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    status: str
    updated_at: Optional[datetime] = None # For "Last Updated" column
    class Config:
        from_attributes = True