from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from PIL import Image, ImageOps
import io
from sqlalchemy.orm import Session
import logging
import os
import uuid
import shutil
from typing import List
from app.database import get_db
from app.config import settings
from . import service, schemas

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cms", tags=["CMS"])

# --- HOMEPAGE BANNERS ---
@router.get("/banners", response_model=list[schemas.BannerResponse])
def get_banners(db: Session = Depends(get_db)):
    return service.get_banners(db)

@router.post("/banners/upload")
def upload_banner_image(request: Request, file: UploadFile = File(...)):
    UPLOAD_DIR = "uploads/cms/banners"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Resize Image to 1.87 aspect ratio (approx 1000x535)
    try:
        content = file.file.read()
        image = Image.open(io.BytesIO(content))
        
        target_width = 1000
        target_height = int(target_width / 1.87) # ~534
        
        # Use ImageOps.fit to crop/resize maintaining aspect ratio
        processed_image = ImageOps.fit(image, (target_width, target_height), Image.Resampling.LANCZOS)
        
        processed_image.save(file_path, quality=90, optimize=True)
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        # Fallback to saving original
        file.file.seek(0)
        with open(file_path, "wb") as f:
             f.write(file.file.read())

    base_url = str(request.base_url).rstrip("/")
    if base_url.startswith("http://"):
        base_url = base_url.replace("http://", "https://")
    url_path = file_path.replace("\\", "/")
    return {"url": f"{base_url}/{url_path}"}

@router.post("/banners", response_model=schemas.BannerResponse)
def create_banner(banner: schemas.BannerCreate, db: Session = Depends(get_db)):
    return service.create_banner(db, banner.dict())

@router.delete("/banners/{banner_id}")
def delete_banner(banner_id: int, db: Session = Depends(get_db)):
    service.delete_banner(db, banner_id)
    return {"status": "success"}

# Add this under the DELETE /banners/{banner_id} route
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
def upload_category_banner(category_id: int, request: Request, file: UploadFile = File(...)):
    UPLOAD_DIR = "uploads/cms/categories"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = file.filename.split(".")[-1]
    filename = f"cat_{category_id}_{uuid.uuid4().hex[:6]}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    base_url = str(request.base_url).rstrip("/")
    if base_url.startswith("http://"):
        base_url = base_url.replace("http://", "https://")
    url_path = file_path.replace("\\", "/")
    return {"url": f"{base_url}/{url_path}"}

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