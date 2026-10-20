from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="customer", nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    profile_image = Column(String(500), nullable=True)

    # Relationships
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    shops = relationship("Shop", back_populates="owner", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer", foreign_keys="Order.customer_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="user", cascade="all, delete-orphan")
    assigned_deliveries = relationship("Delivery", back_populates="rider", foreign_keys="Delivery.rider_id")


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), default="Home", nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    city = Column(String(100), nullable=False)
    locality = Column(String(150), nullable=False)
    address_line = Column(String(500), nullable=False)
    landmark = Column(String(255), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="addresses")
