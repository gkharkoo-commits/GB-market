from datetime import datetime, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_current_admin,
    get_current_rider,
    get_db,
)
from backend.app.core.permissions import OrderStatus, UserRole
from backend.app.models.delivery import Delivery, DeliveryArea
from backend.app.models.order import OrderStatusHistory
from backend.app.models.user import User
from backend.app.schemas.delivery import (
    DeliveryAreaCreate,
    DeliveryAreaResponse,
    DeliveryAreaUpdate,
    DeliveryResponse,
    DeliveryStatusUpdate,
    RiderAssignRequest,
)

router = APIRouter(prefix="/deliveries", tags=["Deliveries & Riders"])

@router.get("/areas", response_model=List[DeliveryAreaResponse])
def list_delivery_areas(
    active_only: bool = True,
    db: Session = Depends(get_db)
) -> Any:
    """Public/Customer: View serviceable delivery areas and standard delivery charges in Gilgit-Baltistan."""
    query = db.query(DeliveryArea)
    if active_only:
        query = query.filter(DeliveryArea.is_active == True)
    return query.order_by(DeliveryArea.city.asc(), DeliveryArea.name.asc()).all()

@router.post("/areas", response_model=DeliveryAreaResponse, status_code=status.HTTP_201_CREATED)
def create_delivery_area(
    data: DeliveryAreaCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: Add a new supported delivery area and fee."""
    area = DeliveryArea(
        name=data.name.strip(),
        city=data.city.strip(),
        delivery_fee=data.delivery_fee,
        estimated_days=data.estimated_days,
        is_active=data.is_active
    )
    db.add(area)
    db.commit()
    db.refresh(area)
    return area

@router.put("/areas/{area_id}", response_model=DeliveryAreaResponse)
def update_delivery_area(
    area_id: int,
    data: DeliveryAreaUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: Update delivery area fee, estimated days, or active status."""
    area = db.query(DeliveryArea).filter(DeliveryArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Delivery area not found")

    if data.name:
        area.name = data.name.strip()
    if data.city:
        area.city = data.city.strip()
    if data.delivery_fee is not None:
        area.delivery_fee = data.delivery_fee
    if data.estimated_days is not None:
        area.estimated_days = data.estimated_days
    if data.is_active is not None:
        area.is_active = data.is_active

    db.commit()
    db.refresh(area)
    return area

# ----------------- Rider Endpoints -----------------

@router.get("/my-deliveries", response_model=List[DeliveryResponse])
def get_my_deliveries(
    current_user: User = Depends(get_current_rider),
    db: Session = Depends(get_db)
) -> Any:
    """Rider: View only deliveries assigned directly to this rider."""
    deliveries = db.query(Delivery).filter(Delivery.rider_id == current_user.id).order_by(Delivery.created_at.desc()).all()
    return deliveries

@router.put("/{delivery_id}/status", response_model=DeliveryResponse)
def update_delivery_status(
    delivery_id: int,
    data: DeliveryStatusUpdate,
    current_user: User = Depends(get_current_rider),
    db: Session = Depends(get_db)
) -> Any:
    """Rider: Update delivery status (Picked Up, Out for Delivery, Delivered, Delivery Failed)."""
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery record not found")

    # Authorize: rider can only update their own assigned delivery (or admin)
    if delivery.rider_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Forbidden: You are not the assigned rider for this delivery")

    delivery.status = data.status
    if data.notes:
        delivery.rider_notes = data.notes
    if data.failure_reason:
        delivery.failure_reason = data.failure_reason

    now = datetime.now(timezone.utc)
    if data.status == "Picked Up":
        delivery.picked_up_at = now
    elif data.status in ["Delivered", OrderStatus.DELIVERED.value]:
        delivery.completed_at = now
        # Update shop group status
        if delivery.shop_group:
            delivery.shop_group.status = OrderStatus.DELIVERED.value
            # If all shop groups delivered, update overall order
            order = delivery.shop_group.order
            if all(sg.status == OrderStatus.DELIVERED.value for sg in order.shop_groups):
                order.status = OrderStatus.DELIVERED.value
                order.payment_status = "Paid"  # COD payment received upon delivery

    elif data.status in ["Out for Delivery", OrderStatus.OUT_FOR_DELIVERY.value]:
        if delivery.shop_group:
            delivery.shop_group.status = OrderStatus.OUT_FOR_DELIVERY.value
            order = delivery.shop_group.order
            order.status = OrderStatus.OUT_FOR_DELIVERY.value

    # Record history
    if delivery.shop_group:
        history = OrderStatusHistory(
            order_id=delivery.order_id,
            shop_order_group_id=delivery.shop_order_group_id,
            previous_status=None,
            new_status=data.status,
            changed_by_id=current_user.id,
            changed_by_role="rider",
            notes=f"Rider {current_user.full_name} updated delivery to: {data.status}. {data.notes or ''}"
        )
        db.add(history)

    db.commit()
    db.refresh(delivery)
    return delivery

# ----------------- Admin Assignment -----------------

@router.put("/admin/{delivery_id}/assign")
def assign_rider_admin(
    delivery_id: int,
    data: RiderAssignRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: Assign or reassign a rider to a delivery."""
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    rider = db.query(User).filter(User.id == data.rider_id, User.role == UserRole.RIDER.value).first()
    if not rider:
        raise HTTPException(status_code=400, detail="User is not a valid or active delivery rider")

    delivery.rider_id = rider.id
    delivery.status = "Assigned"
    delivery.assigned_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(delivery)
    return {"message": f"Delivery assigned to rider {rider.full_name}", "delivery_id": delivery.id}
