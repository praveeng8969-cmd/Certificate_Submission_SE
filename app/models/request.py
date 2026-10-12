from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, JSON, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class ServiceRequest(Base):
    __tablename__ = "service_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('SUBMITTED', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')",
            name="check_valid_status"
        ),
    )

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    resource_id = Column(String(36), ForeignKey("resources.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=False)
    description = Column(Text, nullable=False)
    reference = Column(String(100), nullable=False)
    base_value = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    service_charge = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    status = Column(String(20), nullable=False, default="SUBMITTED", index=True)
    snapshot_data = Column(JSON, nullable=False)
    idempotency_key = Column(String(100), unique=True, nullable=False, index=True)
    resource_reserved = Column(Boolean, nullable=False, default=True)
    resource_released = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="requests")
    resource = relationship("Resource", back_populates="requests")
    status_history = relationship(
        "RequestStatusHistory",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="RequestStatusHistory.event_at.asc()"
    )
