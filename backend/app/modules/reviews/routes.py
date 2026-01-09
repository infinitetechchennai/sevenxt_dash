from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.modules.reviews import models, schemas
from app.modules.products.models import Product

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)

def update_product_rating(db: Session, product_id: str):
    """Recalculate average rating and review count for a product."""
    result = db.query(
        func.avg(models.ProductReview.rating),
        func.count(models.ProductReview.id)
    ).filter(models.ProductReview.product_id == product_id).first()
    
    avg_rating, count = result
    avg_rating = float(avg_rating) if avg_rating else 0.0
    
    # Update product
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.rating = avg_rating
        product.reviews = count
        db.commit()

@router.post("/", response_model=schemas.ProductReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(review: schemas.ProductReviewCreate, db: Session = Depends(get_db)):
    # Verify product exists
    product = db.query(Product).filter(Product.id == review.product_id).first()
    if not product:
         raise HTTPException(status_code=404, detail="Product not found")

    new_review = models.ProductReview(**review.dict())
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    
    # Update product stats
    update_product_rating(db, review.product_id)
    
    return new_review

@router.get("/product/{product_id}", response_model=List[schemas.ProductReviewResponse])
def get_reviews_by_product(product_id: str, db: Session = Depends(get_db)):
    reviews = db.query(models.ProductReview).filter(models.ProductReview.product_id == product_id).all()
    return reviews

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: str, db: Session = Depends(get_db)):
    review = db.query(models.ProductReview).filter(models.ProductReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
        
    product_id = review.product_id
    db.delete(review)
    db.commit()
    
    # Update product stats
    update_product_rating(db, product_id)
