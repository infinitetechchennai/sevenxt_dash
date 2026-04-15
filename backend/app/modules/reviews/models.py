from sqlalchemy import Column, String, Numeric, Text, TIMESTAMP, func, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class ProductReview(Base):
    __tablename__ = "product_reviews"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_id = Column(String(50), nullable=False, index=True)
    user_id = Column(String(255), nullable=False)
    rating = Column(Numeric(2, 1), CheckConstraint('rating >= 0 AND rating <= 5.0'), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
