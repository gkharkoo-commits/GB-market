from datetime import datetime, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_current_admin,
    get_db,
    record_audit,
)
from backend.app.core.permissions import (
    CancellationStatus,
    OrderStatus,
    ProductStatus,
    ShopVerificationStatus,
    UserRole,
)
from backend.app.models.audit import AuditLog
from backend.app.models.complaint import Complaint
from backend.app.models.delivery import Delivery
from backend.app.models.order import CancellationRequest, Order, OrderStatusHistory
from backend.app.models.product import Product
from backend.app.models.setting import MarketplaceSetting
from backend.app.models.shop import Shop
from backend.app.models.user import User
from backend.app.schemas.admin import (
    AuditLogResponse,
    DashboardStatsResponse,
    MarketplaceSettingResponse,
    MarketplaceSettingUpdate,
)
from backend.app.schemas.user import UserResponse

router = APIRouter(prefix="/admin", tags=["Administrator Operations"])

@router.get("/dashboard-stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: Aggregate operational and business statistics."""
    total_sales = db.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
        Order.status != OrderStatus.CANCELLED.value
    ).scalar() or 0.0

    total_orders = db.query(Order).count()
    total_customers = db.query(User).filter(User.role == UserRole.CUSTOMER.value).count()
    total_shops = db.query(Shop).count()
    pending_shops_count = db.query(Shop).filter(
        Shop.verification_status == ShopVerificationStatus.PENDING.value
    ).count()
    active_products_count = db.query(Product).filter(
        Product.status == ProductStatus.ACTIVE.value
    ).count()
    active_deliveries_count = db.query(Delivery).filter(
        Delivery.status.in_(["Assigned", "Picked Up", "Out for Delivery"])
    ).count()
    pending_complaints_count = db.query(Complaint).filter(
        Complaint.status.in_(["Open", "In Progress"])
    ).count()

    recent_orders = (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "total_sales": float(total_sales),
        "total_orders": total_orders,
        "total_customers": total_customers,
        "total_shops": total_shops,
        "pending_shops_count": pending_shops_count,
        "active_products_count": active_products_count,
        "active_deliveries_count": active_deliveries_count,
        "pending_complaints_count": pending_complaints_count,
        "recent_orders": [
            {
                "id": o.id,
                "order_number": o.order_number,
                "customer_name": o.customer_name,
                "total_amount": float(o.total_amount),
                "status": o.status,
                "created_at": o.created_at.isoformat()
            }
            for o in recent_orders
        ]
    }

# ----------------- User Management -----------------

@router.get("/users", response_model=List[UserResponse])
def list_users_admin(
    role: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: List registered users with role filtering."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role.lower())
    return query.order_by(User.created_at.desc()).all()

@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    is_active: bool,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: Activate or suspend a user account."""
    if user_id == current_admin.id and not is_active:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own administrator account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = is_active
    db.commit()

    record_audit(
        db=db,
        actor=current_admin,
        action="USER_STATUS_CHANGE",
        entity_type="User",
        entity_id=str(user.id),
        details=f"User {user.email} status changed to is_active={is_active}",
        request=request
    )
    return {"message": f"User status updated to {'active' if is_active else 'suspended'}"}

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: Change user role (customer, shopkeeper, rider, admin)."""
    valid_roles = [r.value for r in UserRole]
    if role.lower() not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role
    user.role = role.lower()
    db.commit()

    record_audit(
        db=db,
        actor=current_admin,
        action="USER_ROLE_CHANGE",
        entity_type="User",
        entity_id=str(user.id),
        details=f"User {user.email} role changed from {old_role} to {user.role}",
        request=request
    )
    return {"message": f"User role updated to {user.role}"}

# ----------------- Cancellation Requests Review -----------------

@router.get("/cancellations")
def list_cancellation_requests_admin(
    status_filter: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: View order cancellation requests."""
    query = db.query(CancellationRequest)
    if status_filter:
        query = query.filter(CancellationRequest.status == status_filter)
    requests = query.order_by(CancellationRequest.created_at.desc()).all()

    return [
        {
            "id": r.id,
            "order_id": r.order_id,
            "order_number": r.order.order_number if r.order else "",
            "customer_name": r.order.customer_name if r.order else "",
            "reason": r.reason,
            "status": r.status,
            "admin_notes": r.admin_notes,
            "created_at": r.created_at,
            "reviewed_at": r.reviewed_at
        }
        for r in requests
    ]

@router.put("/cancellations/{req_id}/review")
def review_cancellation_request(
    req_id: int,
    decision: str,  # "Approved" or "Rejected"
    admin_notes: Optional[str] = None,
    request: Request = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: Approve or reject cancellation request. If approved, releases stock."""
    cancel_req = db.query(CancellationRequest).filter(CancellationRequest.id == req_id).first()
    if not cancel_req:
        raise HTTPException(status_code=404, detail="Cancellation request not found")

    decision_norm = decision.capitalize()
    if decision_norm not in ["Approved", "Rejected"]:
        raise HTTPException(status_code=400, detail="Decision must be 'Approved' or 'Rejected'")

    cancel_req.status = decision_norm
    cancel_req.admin_notes = admin_notes
    cancel_req.reviewed_by_id = current_admin.id
    cancel_req.reviewed_at = datetime.now(timezone.utc)

    order = cancel_req.order
    if decision_norm == "Approved":
        order.status = OrderStatus.CANCELLED.value
        order.cancellation_reason = f"Cancellation approved: {cancel_req.reason}"

        # Restore inventory
        for item in order.items:
            if item.product:
                item.product.stock_quantity += item.quantity
                if item.product.status == ProductStatus.OUT_OF_STOCK.value:
                    item.product.status = ProductStatus.ACTIVE.value

        for sg in order.shop_groups:
            sg.status = OrderStatus.CANCELLED.value
            sg.cancellation_reason = cancel_req.reason
    else:
        # Revert order back to previous valid processing status
        order.status = OrderStatus.CONFIRMED.value

    history = OrderStatusHistory(
        order_id=order.id,
        previous_status=OrderStatus.CANCELLATION_REQUESTED.value,
        new_status=order.status,
        changed_by_id=current_admin.id,
        changed_by_role="admin",
        notes=f"Admin {current_admin.full_name} {decision_norm.lower()} cancellation. Notes: {admin_notes or ''}"
    )
    db.add(history)
    db.commit()

    return {"message": f"Cancellation request {decision_norm.lower()} successfully"}

# ----------------- Audit Logs -----------------

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = 50,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: View immutable system security and activity audit records."""
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()

# ----------------- Settings & Commission -----------------

@router.get("/settings", response_model=List[MarketplaceSettingResponse])
def get_settings(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: View marketplace settings."""
    return db.query(MarketplaceSetting).all()

@router.put("/settings/{key}", response_model=MarketplaceSettingResponse)
def update_setting(
    key: str,
    data: MarketplaceSettingUpdate,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: Update a configuration value (e.g. commission_percent, delivery_fee)."""
    setting = db.query(MarketplaceSetting).filter(MarketplaceSetting.key == key).first()
    if not setting:
        setting = MarketplaceSetting(key=key, value=data.value, description=data.description)
        db.add(setting)
    else:
        setting.value = data.value
        if data.description is not None:
            setting.description = data.description

    db.commit()
    db.refresh(setting)

    record_audit(
        db=db,
        actor=current_admin,
        action="SETTING_UPDATE",
        entity_type="MarketplaceSetting",
        entity_id=key,
        details=f"Setting '{key}' updated to '{data.value}'",
        request=request
    )
    return setting
