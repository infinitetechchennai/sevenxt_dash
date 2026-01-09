from sqlalchemy import Column, Integer, String, DateTime, Text, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Exchange(Base):
    __tablename__ = "exchanges"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Exchange Request Details
    reason = Column(String(100), nullable=False)  # 'Damaged', 'Defective', 'Wrong Product', 'Size Issue'
    description = Column(Text, nullable=True)
    proof_image_path = Column(String(500), nullable=True)
    
    # Product Information (from the order - same product being exchanged)
    product_id = Column(String(50), nullable=False)
    product_name = Column(String(255), nullable=False)
    variant_color = Column(String(50), nullable=True)
    quantity = Column(Integer, default=1)
    price = Column(DECIMAL(10, 2), nullable=False)
    
    # Status
    status = Column(String(50), default='Pending', nullable=False, index=True)
    # Status values: Pending, Approved, Return In Transit, Return Received, 
    # Quality Check Passed, Quality Check Failed, New Product Dispatched, Completed, Rejected
    
    # Return Shipment Details (Damaged Product - Customer to Warehouse)
    return_awb_number = Column(String(255), nullable=True)
    return_label_path = Column(String(500), nullable=True)
    return_delivery_status = Column(String(50), nullable=True)  # Delhivery status
    delivery_attempts = Column(Integer, default=0, nullable=True)  # Track failed delivery attempts
    
    # Forward Shipment Details (Replacement Product - Warehouse to Customer)
    new_awb_number = Column(String(255), nullable=True)
    new_label_path = Column(String(500), nullable=True)
    new_delivery_status = Column(String(50), nullable=True)  # Delhivery status
    new_delivery_attempts = Column(Integer, default=0, nullable=True)  # Track failed delivery attempts
    
    # Admin Actions
    admin_notes = Column(Text, nullable=True)
    quality_approved = Column(Integer, nullable=True)  # 1 = approved, 0 = rejected, null = not checked
    quality_check_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    approved_at = Column(DateTime, nullable=True)
    quality_checked_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationship
    order = relationship("Order", back_populates="exchanges")

    @property
    def customer_name(self):
        return self.order.customer_name if self.order else "Unknown"

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "customer_name": self.order.customer_name if self.order else "Unknown",
            "reason": self.reason,
            "description": self.description,
            "proof_image_path": self.proof_image_path,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "variant_color": self.variant_color,
            "quantity": self.quantity,
            "price": float(self.price) if self.price else None,
            "status": self.status,
            "return_awb_number": self.return_awb_number,
            "return_label_path": self.return_label_path,
            "return_delivery_status": self.return_delivery_status,
            "new_awb_number": self.new_awb_number,
            "new_label_path": self.new_label_path,
            "new_delivery_status": self.new_delivery_status,
            "admin_notes": self.admin_notes,
            "quality_approved": self.quality_approved,
            "quality_check_notes": self.quality_check_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "quality_checked_at": self.quality_checked_at.isoformat() if self.quality_checked_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
