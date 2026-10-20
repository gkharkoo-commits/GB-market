from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class MarketplaceSettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None

class MarketplaceSettingResponse(BaseModel):
    id: int
    key: str
    value: str
    description: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    actor_id: Optional[int]
    actor_email: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardStatsResponse(BaseModel):
    total_sales: float
    total_orders: int
    total_customers: int
    total_shops: int
    pending_shops_count: int
    active_products_count: int
    active_deliveries_count: int
    pending_complaints_count: int
    recent_orders: List[Dict[str, Any]] = []
