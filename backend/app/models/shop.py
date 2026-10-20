from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, TimestampMixin

class Shop(Base, TimestampMixin):
    __tablename__ = "shops"

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(200), index=True, nullable=False)
    slug = Column(String(220), unique=True, index=True, nullable=False)
    owner_name = Column(String(200), nullable=False)
    phone = Column(String(50), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    locality = Column(String(150), nullable=False)
    address = Column(String(500), nullable=False)
    landmark = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    opening_hours = Column(String(200), default="09:00 AM - 09:00 PM", nullable=False)
    available_delivery_methods = Column(String(200), default="Store Pickup, Standard Delivery", nullable=False)

    # Verification Images & Status
    exterior_image = Column(String(500), nullable=False)
    interior_image = Column(String(500), nullable=True)
    owner_image = Column(String(500), nullable=True)
    verification_status = Column(String(50), default="pending", nullable=False, index=True)  # pending, approved, rejected, suspended
    verification_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    commission_rate = Column(Float, nullable=True)  # custom rate if overridden, else default

    # Relationships
    owner = relationship("User", back_populates="shops")
    category = relationship("Category", back_populates="shops")
    products = relationship("Product", back_populates="shop", cascade="all, delete-orphan")
    verification_documents = relationship("ShopVerificationDoc", back_populates="shop", cascade="all, delete-orphan")
    order_groups = relationship("ShopOrderGroup", back_populates="shop")


class ShopVerificationDoc(Base):
    __tablename__ = "shop_verification_docs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(100), nullable=False)  # CNIC, Trade License, NTN, Utility Bill
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    shop = relationship("Shop", back_populates="verification_documents")
