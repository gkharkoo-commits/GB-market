from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class OrderItemResponse(BaseModel):
    id: int
    product_id: Optional[int]
    product_title: str
    product_image: Optional[str]
    unit_price: float
    quantity: int
    subtotal: float

    class Config:
        from_attributes = True

class OrderStatusHistoryResponse(BaseModel):
    id: int
    previous_status: Optional[str]
    new_status: str
    changed_by_role: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ShopOrderGroupResponse(BaseModel):
    id: int
    order_id: int
    shop_id: int
    shop_name: Optional[str] = None
    subtotal: float
    commission_amount: float
    seller_payout: float
    status: str
    cancellation_reason: Optional[str] = None
    items: List[OrderItemResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    # Customer provides delivery information & selected address or manual input
    address_id: Optional[int] = None
    delivery_name: str = Field(..., min_length=2)
    delivery_phone: str = Field(..., min_length=10)
    delivery_city: str = Field(..., min_length=2)
    delivery_locality: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=5)
    delivery_landmark: Optional[str] = None
    customer_notes: Optional[str] = None
    payment_method: str = "Cash on Delivery"

class OrderResponse(BaseModel):
    id: int
    order_number: str
    customer_id: int
    customer_name: str
    customer_phone: str
    delivery_city: str
    delivery_locality: str
    delivery_address: str
    delivery_landmark: Optional[str] = None
    customer_notes: Optional[str] = None
    subtotal: float
    delivery_fee: float
    total_amount: float
    payment_method: str
    payment_status: str
    status: str
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    shop_groups: List[ShopOrderGroupResponse] = []
    items: List[OrderItemResponse] = []
    status_history: List[OrderStatusHistoryResponse] = []

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

class CancellationRequestCreate(BaseModel):
    order_id: int
    shop_order_group_id: Optional[int] = None
    reason: str = Field(..., min_length=5)

class CancellationRequestResponse(BaseModel):
    id: int
    order_id: int
    shop_order_group_id: Optional[int] = None
    requested_by_id: int
    reason: str
    status: str
    admin_notes: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
