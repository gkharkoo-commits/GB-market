from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_order_group_id = Column(Integer, ForeignKey("shop_order_groups.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    rider_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    pickup_address = Column(String(500), nullable=False)
    delivery_address = Column(String(500), nullable=False)
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(50), nullable=False)

    status = Column(String(50), default="Pending Assignment", nullable=False, index=True)
    rider_notes = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)

    assigned_at = Column(DateTime, nullable=True)
    picked_up_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    shop_group = relationship("ShopOrderGroup", back_populates="delivery")
    rider = relationship("User", back_populates="assigned_deliveries", foreign_keys=[rider_id])


class DeliveryArea(Base):
    __tablename__ = "delivery_areas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    city = Column(String(100), nullable=False, index=True)
    delivery_fee = Column(Numeric(10, 2), default=150.00, nullable=False)
    estimated_days = Column(Integer, default=2, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
