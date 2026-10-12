from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RequestStatusHistory(Base):
    __tablename__ = "request_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reference_id = Column(String(36), ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=False)
    event_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    request = relationship("ServiceRequest", back_populates="status_history")
    actor = relationship("User")
