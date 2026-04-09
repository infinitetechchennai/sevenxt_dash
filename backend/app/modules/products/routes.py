from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from app.database import get_db
from app.modules.auth.routes import get_current_employee
from app.modules.auth.models import EmployeeUser
from . import schemas, service
from datetime import datetime
from app.modules.activity_logs.service import log_activity
from app.modules.reviews.models import ProductReview
import os
import uuid
from pathlib import Path

router = APIRouter(prefix="/products", tags=["Products"])

# ... (keep existing imports and code) ...

@router.get("")
def read_products(
    skip: int = 0, 
    limit: int = 10000,
    db: Session = Depends(get_db),
    # current_user: EmployeeUser = Depends(get_current_employee) 
):
    try:
        print(f"DEBUG ROUTE: Fetching products with skip={skip}, limit={limit}")
        products = service.get_products(db, skip=skip, limit=limit)
        print(f"DEBUG ROUTE: Successfully fetched {len(products)} products")
        
        # Manually serialize to ensure all fields are included
        result = []
        for product in products:
            try:
                # DEBUG: Check review count first
                p_id_str = str(product.id)
                review_count = db.query(ProductReview).filter(ProductReview.product_id == p_id_str).count()
                print(f"DEBUG: Product {p_id_str} has {review_count} reviews in DB. Fetching latest...")
                
                # Calculate average rating from reviews
                if review_count > 0:
                    from sqlalchemy import func
                    avg_rating_result = db.query(func.avg(ProductReview.rating)).filter(
                        ProductReview.product_id == p_id_str
                    ).scalar()
                    avg_rating = float(avg_rating_result) if avg_rating_result else 0.0
                    
                    latest_review = db.query(ProductReview).filter(
                        ProductReview.product_id == p_id_str
                    ).order_by(desc(ProductReview.created_at)).first()
                    print(f"DEBUG: Latest review for {p_id_str}: {latest_review.comment if latest_review else 'None'}, Avg Rating: {avg_rating}")
                else:
                    avg_rating = 0.0
                    latest_review = None
                    
            except Exception as e:
                print(f"DEBUG: Error fetching review for product {product.id}: {e}")
                avg_rating = 0.0
                latest_review = None
                review_count = 0
            
            product_dict = {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "colors": product.colors,
                "brandName": product.brand_name,
                
                "b2cPrice": product.b2c_price,
                "compareAtPrice": product.compare_at_price,
                "b2bPrice": product.b2b_price,
                "b2cOfferPercentage": product.b2c_active_offer if product.b2c_active_offer is not None else 0.0,
                "b2cDiscount": product.b2c_discount if product.b2c_discount is not None else 0.0,
                "b2cOfferPrice": product.b2c_offer_price if product.b2c_offer_price is not None else 0.0,
                "b2cOfferStartDate": (product.b2c_offer_start_date.isoformat() if hasattr(product.b2c_offer_start_date, 'isoformat') else str(product.b2c_offer_start_date)) if product.b2c_offer_start_date else None,
                "b2cOfferEndDate": (product.b2c_offer_end_date.isoformat() if hasattr(product.b2c_offer_end_date, 'isoformat') else str(product.b2c_offer_end_date)) if product.b2c_offer_end_date else None,
                "b2bOfferPercentage": product.b2b_active_offer if product.b2b_active_offer is not None else 0.0,
                "b2bDiscount": product.b2b_discount if product.b2b_discount is not None else 0.0,
                "b2bOfferPrice": product.b2b_offer_price if product.b2b_offer_price is not None else 0.0,
                "b2bOfferStartDate": (product.b2b_offer_start_date.isoformat() if hasattr(product.b2b_offer_start_date, 'isoformat') else str(product.b2b_offer_start_date)) if product.b2b_offer_start_date else None,
                "b2bOfferEndDate": (product.b2b_offer_end_date.isoformat() if hasattr(product.b2b_offer_end_date, 'isoformat') else str(product.b2b_offer_end_date)) if product.b2b_offer_end_date else None,
                "info": product.info,
                "description": product.description,
                "status": product.status,
                "stock": product.stock,
                "image": product.image,
                "rating": avg_rating,  # Use calculated average rating from reviews
                "reviews": review_count,  # Use the count we already calculated above
                "latestReview": latest_review.comment if latest_review else None,
                
                # Tax and Compliance
                "sgst": product.sgst if product.sgst is not None else 0.0,
                "cgst": product.cgst if product.cgst is not None else 0.0,
                "hsn": product.hsn,
                # "returnPolicy": product.return_policy,
                
                # Dimensions
                "height": product.height if product.height is not None else 0.0,
                "weight": product.weight if product.weight is not None else 0.0,
                "breadth": product.breadth if product.breadth is not None else 0.0,
                "length": product.length if product.length is not None else 0.0,
                
                "createdAt": (product.created_at.isoformat() if hasattr(product.created_at, 'isoformat') else str(product.created_at)) if product.created_at else None,
                "updatedAt": (product.updated_at.isoformat() if hasattr(product.updated_at, 'isoformat') else str(product.updated_at)) if product.updated_at else None,
                "attributes": [{"name": attr.name, "value": attr.value} for attr in product.attributes],
                "variants": [{"color": v.color, "colorCode": v.color_code, "stock": v.stock} for v in product.variants]
            }
            result.append(product_dict)
        
        return result
    except Exception as e:
        print(f"ERROR in read_products route: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@router.get("/{product_id}", response_model=schemas.ProductResponse, response_model_by_alias=True)
def read_product(
    product_id: str, 
    db: Session = Depends(get_db),
    # current_user: EmployeeUser = Depends(get_current_employee)
):
    db_product = service.get_product(db, product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.post("", response_model=schemas.ProductResponse, response_model_by_alias=True)
def create_product(
    product: schemas.ProductCreate, 
    db: Session = Depends(get_db),
    current_user: EmployeeUser = Depends(get_current_employee)
):
    new_product = service.create_product(db=db, product=product)
    
    # Log activity
    log_activity(
        db=db,
        action="Created Product",
        module="Products",
        user_name=current_user.name if current_user else "System",
        user_type=current_user.role if current_user else "System",
        details=f"Created new product: {product.name} (ID: {new_product.id})",
        status="Success",
        affected_entity_type="Product",
        affected_entity_id=str(new_product.id)
    )
    
    return new_product

@router.put("/{product_id}", response_model=schemas.ProductResponse, response_model_by_alias=True)
def update_product(
    product_id: str, 
    product: schemas.ProductUpdate, 
    db: Session = Depends(get_db),
    current_user: EmployeeUser = Depends(get_current_employee)
):
    db_product = service.update_product(db=db, product_id=product_id, product=product)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Log activity
    log_activity(
        db=db,
        action="Updated Product",
        module="Products",
        user_name=current_user.name if current_user else "System",
        user_type=current_user.role if current_user else "System",
        details=f"Updated product: {db_product.name} (ID: {product_id})",
        status="Success",
        affected_entity_type="Product",
        affected_entity_id=product_id
    )
    
    return db_product

@router.delete("/{product_id}")
def delete_product(
    product_id: str, 
    db: Session = Depends(get_db),
    current_user: EmployeeUser = Depends(get_current_employee)
):
    success = service.delete_product(db=db, product_id=product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Log activity
    log_activity(
        db=db,
        action="Deleted Product",
        module="Products",
        user_name=current_user.name if current_user else "System",
        user_type=current_user.role if current_user else "System",
        details=f"Deleted product with ID: {product_id}",
        status="Success",
        affected_entity_type="Product",
        affected_entity_id=product_id
    )
    
    return {"status": "success"}

@router.post("/upload-image")
async def upload_product_image(
    file: UploadFile = File(...)
):
    """
    Upload a product image to Cloudinary and return the URL.
    Resizes image to max width 420px before uploading.
    """
    try:
        # Validate file type
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        file_extension = Path(file.filename).suffix.lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
            )

        contents = await file.read()

        from app.utils.cloudinary_upload import upload_image_to_cloudinary
        image_url = upload_image_to_cloudinary(
            file_bytes=contents,
            folder="sevenxt/products",
            resize_width=420,
            quality=85,
        )

        return {
            "status": "success",
            "url": image_url,
            "filename": file.filename
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

@router.post("/import")
async def import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: EmployeeUser = Depends(get_current_employee)
):
    """Bulk import products from Excel/CSV file"""
    # Endpoint for bulk product import via Excel/CSV upload
    try:
        # Read file contents
        contents = await file.read()
        
        # Process the import
        result = service.process_bulk_import(db, contents, verbose=True)
        
        # Log activity
        log_activity(
            db=db,
            action="Bulk Import Products",
            module="Products",
            user_name=current_user.name if current_user else "System",
            user_type=current_user.role if current_user else "System",
            details=f"Imported {result['success']} products ({result['created']} created, {result['updated']} updated, {result['failed']} failed)",
            status="Success" if result['failed'] == 0 else "Partial Success",
            affected_entity_type="Product",
            affected_entity_id="bulk_import"
        )
        
        return {
            "status": "success",
            "message": f"Import completed: {result['success']} successful, {result['failed']} failed",
            "details": result
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
