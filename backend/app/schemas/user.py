from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

class AddressBase(BaseModel):
    title: str = "Home"
    full_name: str
    phone: str
    city: str
    locality: str
    address_line: str
    landmark: Optional[str] = None
    is_default: bool = False

class AddressCreate(AddressBase):
    pass

class AddressResponse(AddressBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    phone: str
    full_name: str
    role: str = "customer"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    profile_image: Optional[str] = None

class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    new_password_confirm: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    profile_image: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UserDetailResponse(UserResponse):
    addresses: List[AddressResponse] = []
