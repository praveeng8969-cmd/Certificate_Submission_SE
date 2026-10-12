from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # "USER" or "ADMINISTRATOR"
    status = Column(String(20), nullable=False, default="ACTIVE")  # "ACTIVE" or "INACTIVE"
    phone = Column(String(15), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    requests = relationship("ServiceRequest", back_populates="user", cascade="all, delete-orphan")
