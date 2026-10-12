from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Resource(Base):
    __tablename__ = "resources"
    __table_args__ = (
        CheckConstraint("capacity >= 0", name="check_positive_capacity"),
    )

    id = Column(String(36), primary_key=True, index=True)
    service_name = Column(String(150), nullable=False)
    capacity = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="ACTIVE")  # "ACTIVE" or "INACTIVE"
    base_value = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    charge_applicable = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    requests = relationship("ServiceRequest", back_populates="resource")
