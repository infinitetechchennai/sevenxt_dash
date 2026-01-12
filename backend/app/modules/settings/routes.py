from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from . import schemas, service
from app.modules.auth.routes import get_current_employee
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/stock-alerts", response_model=schemas.StockAlertSettings)
def get_stock_alert_settings(db: Session = Depends(get_db)):
    """Get current stock alert settings"""
    try:
        settings = service.get_stock_alert_settings(db)
        return settings
    except Exception as e:
        logger.error(f"Error fetching stock alert settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/stock-alerts", response_model=schemas.StockAlertSettings)
def update_stock_alert_settings(
    settings: schemas.StockAlertUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_employee)
):
    """Update stock alert settings"""
    try:
        updated_settings = service.update_stock_alert_settings(
            db, settings, current_user.id
        )
        logger.info(f"Stock alert settings updated by {current_user.name}")
        return updated_settings
    except Exception as e:
        logger.error(f"Error updating stock alert settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/low-stock-products")
def get_low_stock_products(db: Session = Depends(get_db)):
    """Get list of products with stock below threshold"""
    try:
        products = service.get_low_stock_products(db)
        return {
            "count": len(products),
            "products": products
        }
    except Exception as e:
        logger.error(f"Error fetching low stock products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications")
def get_notification_settings(db: Session = Depends(get_db)):
    """Get notification settings"""
    try:
        settings = service.get_settings_by_category(db, 'notifications')
        result = {
            'new_order_enabled': True,
            'refund_enabled': True,
            'exchange_enabled': True,
            'low_stock_enabled': True,
            'delivery_update_enabled': True
        }
        for s in settings:
            if s.key in result:
                result[s.key] = s.value.lower() == 'true'
        return result
    except Exception as e:
        logger.error(f"Error fetching notification settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/notifications")
def update_notification_settings(
    settings: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_employee)
):
    """Update notification settings"""
    try:
        for key, value in settings.items():
            service.create_or_update_setting(
                db, 'notifications', key, str(value), 'boolean',
                f'Enable {key.replace("_", " ")} notifications',
                current_user.id
            )
        logger.info(f"Notification settings updated by {current_user.name}")
        return settings
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{category}")
def get_settings_by_category(
    category: str,
    db: Session = Depends(get_db)
):
    """Get all settings for a specific category"""
    try:
        settings = service.get_settings_by_category(db, category)
        return [
            {
                "key": s.key,
                "value": s.value,
                "data_type": s.data_type,
                "description": s.description
            }
            for s in settings
        ]
    except Exception as e:
        logger.error(f"Error fetching settings for category {category}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
