from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class DeliveryAreaBase(BaseModel):
    name: str
    city: str
    delivery_fee: float = Field(..., ge=0)
    estimated_days: int = Field(2, ge=1)
    is_active: bool = True

class DeliveryAreaCreate(DeliveryAreaBase):
    pass

class DeliveryAreaUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    delivery_fee: Optional[float] = None
    estimated_days: Optional[int] = None
    is_active: Optional[bool] = None

class DeliveryAreaResponse(DeliveryAreaBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DeliveryResponse(BaseModel):
    id: int
    order_id: int
    shop_order_group_id: int
    rider_id: Optional[int]
    pickup_address: str
    delivery_address: str
    customer_name: str
    customer_phone: str
    status: str
    rider_notes: Optional[str]
    failure_reason: Optional[str]
    assigned_at: Optional[datetime]
    picked_up_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class DeliveryStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    failure_reason: Optional[str] = None

class RiderAssignRequest(BaseModel):
    rider_id: int
