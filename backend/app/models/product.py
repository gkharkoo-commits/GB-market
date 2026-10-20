from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import Base, TimestampMixin

class Product(Base, TimestampMixin):
    __tablename__ = "products"

    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    slug = Column(String(280), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2), nullable=True)
    stock_quantity = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="active", nullable=False, index=True)  # draft, active, out_of_stock, archived
    is_featured = Column(Boolean, default=False, nullable=False)
    unit = Column(String(50), default="item", nullable=False)  # kg, pack, piece, box

    # Relationships
    shop = relationship("Shop", back_populates="products")
    category = relationship("Category", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.display_order")
    cart_items = relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    product = relationship("Product", back_populates="images")
