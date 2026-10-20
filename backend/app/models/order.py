from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, TimestampMixin

class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    order_number = Column(String(50), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(50), nullable=False)
    customer_email = Column(String(255), nullable=True)

    # Delivery Snapshot
    delivery_city = Column(String(100), nullable=False)
    delivery_locality = Column(String(150), nullable=False)
    delivery_address = Column(String(500), nullable=False)
    delivery_landmark = Column(String(255), nullable=True)
    customer_notes = Column(Text, nullable=True)

    # Financials (Snapshot)
    subtotal = Column(Numeric(10, 2), nullable=False)
    delivery_fee = Column(Numeric(10, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), default="Cash on Delivery", nullable=False)
    payment_status = Column(String(50), default="Pending", nullable=False)

    # Workflow Status
    status = Column(String(50), default="Pending Confirmation", nullable=False, index=True)
    cancellation_reason = Column(Text, nullable=True)

    # Relationships
    customer = relationship("User", back_populates="orders", foreign_keys=[customer_id])
    shop_groups = relationship("ShopOrderGroup", back_populates="order", cascade="all, delete-orphan")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan", order_by="OrderStatusHistory.created_at")
    cancellation_requests = relationship("CancellationRequest", back_populates="order", cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="order")


class ShopOrderGroup(Base, TimestampMixin):
    """Fulfillment group per vendor/shop for multi-seller orders."""
    __tablename__ = "shop_order_groups"

    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="RESTRICT"), nullable=False, index=True)

    subtotal = Column(Numeric(10, 2), nullable=False)
    commission_rate = Column(Float, default=5.0, nullable=False)
    commission_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    seller_payout = Column(Numeric(10, 2), default=0.00, nullable=False)
    status = Column(String(50), default="Pending Confirmation", nullable=False, index=True)
    cancellation_reason = Column(Text, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="shop_groups")
    shop = relationship("Shop", back_populates="order_groups")
    items = relationship("OrderItem", back_populates="shop_group", cascade="all, delete-orphan")
    delivery = relationship("Delivery", back_populates="shop_group", uselist=False, cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_order_group_id = Column(Integer, ForeignKey("shop_order_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)

    # Immutable Snapshot
    product_title = Column(String(255), nullable=False)
    product_image = Column(String(500), nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    shop_group = relationship("ShopOrderGroup", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_order_group_id = Column(Integer, ForeignKey("shop_order_groups.id", ondelete="CASCADE"), nullable=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    changed_by_role = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    order = relationship("Order", back_populates="status_history")


class CancellationRequest(Base):
    __tablename__ = "cancellation_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_order_group_id = Column(Integer, ForeignKey("shop_order_groups.id", ondelete="CASCADE"), nullable=True)
    requested_by_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="Pending", nullable=False)  # Pending, Approved, Rejected
    admin_notes = Column(Text, nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="cancellation_requests")
