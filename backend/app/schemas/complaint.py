from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ComplaintCreate(BaseModel):
    order_id: Optional[int] = None
    subject: str = Field(..., min_length=3, max_length=255)
    message: str = Field(..., min_length=10)

class ComplaintAdminReply(BaseModel):
    status: str
    admin_response: str

class ComplaintResponse(BaseModel):
    id: int
    user_id: int
    order_id: Optional[int]
    subject: str
    message: str
    status: str
    admin_response: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
