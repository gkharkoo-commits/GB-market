from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(1, ge=1)

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1)

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    product_title: str
    product_price: float
    product_image: Optional[str] = None
    shop_id: int
    shop_name: str
    available_stock: int
    subtotal: float

class CartResponse(BaseModel):
    id: int
    total_items: int
    subtotal: float
    items: List[CartItemResponse] = []
