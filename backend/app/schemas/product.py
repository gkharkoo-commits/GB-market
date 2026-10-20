from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class ProductImageCreate(BaseModel):
    image_url: str
    is_primary: bool = False
    display_order: int = 0

class ProductImageResponse(BaseModel):
    id: int
    product_id: int
    image_url: str
    is_primary: bool
    display_order: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    category_id: Optional[int] = None
    description: str = Field(..., min_length=5)
    price: float = Field(..., gt=0)
    original_price: Optional[float] = None
    stock_quantity: int = Field(..., ge=0)
    unit: str = "item"
    is_featured: bool = False

class ProductCreate(ProductBase):
    shop_id: Optional[int] = None  # Inferred from seller if not provided
    image_urls: List[str] = []

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None
    unit: Optional[str] = None
    is_featured: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    shop_id: int
    slug: str
    status: str
    created_at: datetime
    updated_at: datetime
    images: List[ProductImageResponse] = []
    shop_name: Optional[str] = None
    category_name: Optional[str] = None

    class Config:
        from_attributes = True

class ProductFilterParams(BaseModel):
    search: Optional[str] = None
    category_id: Optional[int] = None
    shop_id: Optional[int] = None
    city: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    in_stock_only: Optional[bool] = False
    is_featured: Optional[bool] = None
    sort_by: Optional[str] = "newest"  # newest, price_asc, price_desc, popular
    page: int = 1
    limit: int = 20
