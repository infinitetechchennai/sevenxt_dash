from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from PIL import Image, ImageOps
import io
from sqlalchemy.orm import Session
import logging
import uuid
from typing import List
from app.database import get_db
from app.config import settings
from app.utils.cloudinary_upload import upload_image_to_cloudinary
from . import service, schemas

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cms", tags=["CMS"])

# --- HOMEPAGE BANNERS ---
@router.get("/banners", response_model=list[schemas.BannerResponse])
def get_banners(db: Session = Depends(get_db)):
    return service.get_banners(db)

@router.post("/banners/upload")
def upload_banner_image(file: UploadFile = File(...)):
    try:
        content = file.file.read()
        image_url = upload_image_to_cloudinary(
            file_bytes=content,
            folder="sevenxt/cms/banners",
            aspect_ratio=(1000, 535),
            quality=90,
        )
        return {"url": image_url}
    except Exception as e:
        logger.error(f"Banner upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Banner upload failed: {str(e)}")

@router.post("/banners", response_model=schemas.BannerResponse)
def create_banner(banner: schemas.BannerCreate, db: Session = Depends(get_db)):
    return service.create_banner(db, banner.dict())

@router.delete("/banners/{banner_id}")
def delete_banner(banner_id: int, db: Session = Depends(get_db)):
    service.delete_banner(db, banner_id)
    return {"status": "success"}

@router.put("/banners/{banner_id}", response_model=schemas.BannerResponse)
def update_banner(banner_id: int, banner: schemas.BannerCreate, db: Session = Depends(get_db)):
    updated_banner = service.update_banner(db, banner_id, banner.dict())
    if not updated_banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    return updated_banner

# --- CATEGORY BANNERS ---
@router.get("/category-banners", response_model=List[schemas.CategoryBannerResponse])
def get_all_category_banners(db: Session = Depends(get_db)):
    return service.get_category_banners(db)

@router.post("/category-banners/{category_id}/upload")
def upload_category_banner(category_id: int, file: UploadFile = File(...)):
    try:
        content = file.file.read()
        image_url = upload_image_to_cloudinary(
            file_bytes=content,
            folder="sevenxt/cms/categories",
            quality=90,
        )
        return {"url": image_url}
    except Exception as e:
        logger.error(f"Category banner upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Category banner upload failed: {str(e)}")

@router.put("/category-banners/{category_id}")
def update_category_banner(category_id: int, data: dict, db: Session = Depends(get_db)):
    updated = service.update_category_banner(db, category_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"status": "success", "data": updated}

# --- NOTIFICATIONS & PAGES ---
@router.get("/notifications", response_model=List[schemas.NotificationResponse])
def get_notifications(db: Session = Depends(get_db)):
    return service.get_notifications(db)

@router.post("/notifications", response_model=schemas.NotificationResponse)
def send_notification(notif: schemas.NotificationCreate, db: Session = Depends(get_db)):
    return service.create_notification(db, notif.dict())

@router.get("/app-notifications", response_model=List[schemas.AppNotificationResponse])
def get_app_notifications(db: Session = Depends(get_db)):
    return service.get_app_notifications(db)

@router.post("/app-notifications", response_model=schemas.AppNotificationResponse)
def create_app_notification(notif: schemas.AppNotificationCreate, db: Session = Depends(get_db)):
    return service.create_app_notification(db, notif.dict())


@router.get("/pages", response_model=List[schemas.PageResponse])
def get_pages(db: Session = Depends(get_db)):
    return service.get_pages(db)

@router.put("/pages/{page_id}", response_model=schemas.PageResponse)
def update_page(page_id: int, page: schemas.PageUpdate, db: Session = Depends(get_db)):
    return service.update_page(db, page_id, page.dict())