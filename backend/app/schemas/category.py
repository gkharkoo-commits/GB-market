from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True
    display_order: int = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
