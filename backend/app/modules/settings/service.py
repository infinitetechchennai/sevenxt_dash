from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas
import json

def get_setting(db: Session, category: str, key: str) -> Optional[models.Setting]:
    """Get a specific setting by category and key"""
    return db.query(models.Setting).filter(
        models.Setting.category == category,
        models.Setting.key == key,
        models.Setting.is_active == True
    ).first()

def get_settings_by_category(db: Session, category: str) -> List[models.Setting]:
    """Get all settings for a category"""
    return db.query(models.Setting).filter(
        models.Setting.category == category,
        models.Setting.is_active == True
    ).all()

def create_or_update_setting(
    db: Session, 
    category: str, 
    key: str, 
    value: str, 
    data_type: str = 'string',
    description: str = None,
    updated_by: int = None
) -> models.Setting:
    """Create or update a setting"""
    setting = get_setting(db, category, key)
    
    if setting:
        # Update existing
        setting.value = value
        setting.data_type = data_type
        if description:
            setting.description = description
        setting.updated_by = updated_by
    else:
        # Create new
        setting = models.Setting(
            category=category,
            key=key,
            value=value,
            data_type=data_type,
            description=description,
            updated_by=updated_by
        )
        db.add(setting)
    
    db.commit()
    db.refresh(setting)
    return setting

def get_stock_alert_settings(db: Session) -> dict:
    """Get stock alert settings"""
    settings = get_settings_by_category(db, 'inventory')
    
    result = {
        'low_stock_threshold': 10,  # Default
        'enable_email_alerts': True,
        'enable_dashboard_alerts': True,
        'alert_email': None
    }
    
    for setting in settings:
        if setting.key == 'low_stock_threshold':
            result['low_stock_threshold'] = int(setting.value)
        elif setting.key == 'enable_email_alerts':
            result['enable_email_alerts'] = setting.value.lower() == 'true'
        elif setting.key == 'enable_dashboard_alerts':
            result['enable_dashboard_alerts'] = setting.value.lower() == 'true'
        elif setting.key == 'alert_email':
            result['alert_email'] = setting.value
    
    return result

def update_stock_alert_settings(
    db: Session, 
    settings: schemas.StockAlertUpdate,
    updated_by: int = None
) -> dict:
    """Update stock alert settings"""
    
    if settings.low_stock_threshold is not None:
        create_or_update_setting(
            db, 'inventory', 'low_stock_threshold', 
            str(settings.low_stock_threshold), 'number',
            'Minimum stock level before alert is triggered',
            updated_by
        )
    
    if settings.enable_email_alerts is not None:
        create_or_update_setting(
            db, 'inventory', 'enable_email_alerts',
            str(settings.enable_email_alerts), 'boolean',
            'Send email alerts for low stock',
            updated_by
        )
    
    if settings.enable_dashboard_alerts is not None:
        create_or_update_setting(
            db, 'inventory', 'enable_dashboard_alerts',
            str(settings.enable_dashboard_alerts), 'boolean',
            'Show alerts on dashboard',
            updated_by
        )
    
    if settings.alert_email is not None:
        create_or_update_setting(
            db, 'inventory', 'alert_email',
            settings.alert_email, 'string',
            'Email address to receive stock alerts',
            updated_by
        )
    
    return get_stock_alert_settings(db)

def get_low_stock_products(db: Session) -> List[dict]:
    """Get products with stock below threshold"""
    from app.modules.products.models import Product
    
    settings = get_stock_alert_settings(db)
    threshold = settings['low_stock_threshold']
    
    # Get products with low stock
    products = db.query(Product).filter(
        Product.stock <= threshold
    ).all()
    
    return [{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'stock': p.stock,
        'threshold': threshold,
        'status': 'Out of Stock' if p.stock == 0 else 'Low Stock'
    } for p in products]
