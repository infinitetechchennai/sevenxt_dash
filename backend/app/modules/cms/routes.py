from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
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
def upload_banner_image(file: UploadFile = File(...)):
    UPLOAD_DIR = "uploads/cms/banners"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return {"url": f"http://13.233.199.134:8000/{file_path}"}

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
def upload_category_banner(category_id: int, file: UploadFile = File(...)):
    UPLOAD_DIR = "uploads/cms/categories"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = file.filename.split(".")[-1]
    filename = f"cat_{category_id}_{uuid.uuid4().hex[:6]}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"url": f"http://13.233.199.134:8000/uploads/cms/categories/{filename}"}

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

@router.get("/pages", response_model=List[schemas.PageResponse])
def get_pages(db: Session = Depends(get_db)):
    return service.get_pages(db)

@router.put("/pages/{page_id}", response_model=schemas.PageResponse)
def update_page(page_id: int, page: schemas.PageUpdate, db: Session = Depends(get_db)):
    return service.update_page(db, page_id, page.dict())