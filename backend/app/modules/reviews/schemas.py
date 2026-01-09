from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProductReviewBase(BaseModel):
    product_id: str
    user_id: str
    rating: float = Field(..., ge=0, le=5.0)
    comment: Optional[str] = None

class ProductReviewCreate(ProductReviewBase):
    pass

class ProductReviewResponse(ProductReviewBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
