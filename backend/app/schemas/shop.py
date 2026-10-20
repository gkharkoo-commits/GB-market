from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class ShopVerificationDocResponse(BaseModel):
    id: int
    shop_id: int
    document_type: str
    file_path: str
    original_filename: str
    file_size_bytes: int
    is_verified: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True

class ShopBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    category_id: Optional[int] = None
    owner_name: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(..., min_length=10, max_length=50)
    city: str = Field(..., min_length=2, max_length=100)
    locality: str = Field(..., min_length=2, max_length=150)
    address: str = Field(..., min_length=5, max_length=500)
    landmark: Optional[str] = None
    description: str = Field(..., min_length=10)
    opening_hours: str = "09:00 AM - 09:00 PM"
    available_delivery_methods: str = "Store Pickup, Standard Delivery"

class ShopCreate(ShopBase):
    exterior_image: str
    interior_image: Optional[str] = None
    owner_image: Optional[str] = None

class ShopUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    locality: Optional[str] = None
    address: Optional[str] = None
    landmark: Optional[str] = None
    description: Optional[str] = None
    opening_hours: Optional[str] = None
    available_delivery_methods: Optional[str] = None
    exterior_image: Optional[str] = None
    interior_image: Optional[str] = None
    owner_image: Optional[str] = None

class ShopAdminReview(BaseModel):
    status: str = Field(..., description="approved, rejected, or suspended")
    verification_notes: Optional[str] = None
    commission_rate: Optional[float] = None

class ShopResponse(ShopBase):
    id: int
    owner_id: int
    slug: str
    exterior_image: str
    interior_image: Optional[str] = None
    owner_image: Optional[str] = None
    verification_status: str
    verification_notes: Optional[str] = None
    is_active: bool
    commission_rate: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    verification_documents: List[ShopVerificationDocResponse] = []

    class Config:
        from_attributes = True

class ShopPublicSummary(BaseModel):
    id: int
    name: str
    slug: str
    category_id: Optional[int] = None
    owner_name: str
    city: str
    locality: str
    address: str
    exterior_image: str
    opening_hours: str
    created_at: datetime

    class Config:
        from_attributes = True
