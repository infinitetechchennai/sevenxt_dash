from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class ActivityStatus(str, enum.Enum):
    SUCCESS = "Success"
    FAILED = "Failed"
    WARNING = "Warning"


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=True)  # Can be null for system actions
    user_name = Column(String(255), nullable=True)
    user_type = Column(String(50), nullable=True)  # Admin, Staff, B2B, B2C
    action = Column(String(255), nullable=False)
    module = Column(String(100), nullable=False)  # Users, Orders, Products, etc.
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    status = Column(Enum(ActivityStatus), default=ActivityStatus.SUCCESS)
    affected_entity_type = Column(String(100), nullable=True)  # User, Order, Product, etc.
    affected_entity_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_type": self.user_type,
            "action": self.action,
            "module": self.module,
            "details": self.details,
            "ip_address": self.ip_address,
            "status": self.status.value if self.status else "Success",
            "affected_entity_type": self.affected_entity_type,
            "affected_entity_id": self.affected_entity_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
