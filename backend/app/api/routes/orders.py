from datetime import datetime, timezone
from decimal import Decimal
import secrets
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_current_admin,
    get_current_customer,
    get_current_shopkeeper,
    get_current_user,
    get_db,
    record_audit,
)
from backend.app.core.config import settings
from backend.app.core.permissions import (
    CancellationStatus,
    OrderStatus,
    ProductStatus,
    ShopVerificationStatus,
    UserRole,
)
from backend.app.models.cart import Cart, CartItem
from backend.app.models.delivery import Delivery, DeliveryArea
from backend.app.models.order import (
    CancellationRequest,
    Order,
    OrderItem,
    OrderStatusHistory,
    ShopOrderGroup,
)
from backend.app.models.product import Product
from backend.app.models.shop import Shop
from backend.app.models.user import Address, User
from backend.app.schemas.order import (
    CancellationRequestCreate,
    CancellationRequestResponse,
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
)

router = APIRouter(prefix="/orders", tags=["Orders & Fulfillment"])

def _format_order(order: Order) -> dict:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer_id": order.customer_id,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "customer_email": order.customer_email,
        "delivery_city": order.delivery_city,
        "delivery_locality": order.delivery_locality,
        "delivery_address": order.delivery_address,
        "delivery_landmark": order.delivery_landmark,
        "customer_notes": order.customer_notes,
        "subtotal": float(order.subtotal),
        "delivery_fee": float(order.delivery_fee),
        "total_amount": float(order.total_amount),
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "status": order.status,
        "cancellation_reason": order.cancellation_reason,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "shop_groups": [
            {
                "id": sg.id,
                "order_id": sg.order_id,
                "shop_id": sg.shop_id,
                "shop_name": sg.shop.name if sg.shop else "Shop",
                "subtotal": float(sg.subtotal),
                "commission_amount": float(sg.commission_amount),
                "seller_payout": float(sg.seller_payout),
                "status": sg.status,
                "cancellation_reason": sg.cancellation_reason,
                "created_at": sg.created_at,
                "items": [
                    {
                        "id": item.id,
                        "product_id": item.product_id,
                        "product_title": item.product_title,
                        "product_image": item.product_image,
                        "unit_price": float(item.unit_price),
                        "quantity": item.quantity,
                        "subtotal": float(item.subtotal)
                    }
                    for item in sg.items
                ]
            }
            for sg in order.shop_groups
        ],
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_title": item.product_title,
                "product_image": item.product_image,
                "unit_price": float(item.unit_price),
                "quantity": item.quantity,
                "subtotal": float(item.subtotal)
            }
            for item in order.items
        ],
        "status_history": [
            {
                "id": sh.id,
                "previous_status": sh.previous_status,
                "new_status": sh.new_status,
                "changed_by_role": sh.changed_by_role,
                "notes": sh.notes,
                "created_at": sh.created_at
            }
            for sh in order.status_history
        ]
    }

@router.post("/checkout", status_code=status.HTTP_201_CREATED)
def checkout(
    data: OrderCreate,
    request: Request,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
) -> Any:
    """Customer checkout: validates stock atomically, records price snapshots, splits into shop fulfillment groups, creates COD order."""
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Your shopping cart is empty")

    # Group cart items by shop
    items_by_shop = {}
    for ci in cart.items:
        prod = ci.product
        if not prod or prod.status != ProductStatus.ACTIVE.value:
            raise HTTPException(status_code=400, detail=f"Product '{prod.title if prod else 'Unknown'}' is unavailable")
        
        # Check shop status
        if prod.shop.verification_status != ShopVerificationStatus.APPROVED.value or not prod.shop.is_active:
            raise HTTPException(status_code=400, detail=f"Shop '{prod.shop.name}' is currently not approved to sell")

        # Check real-time stock
        if prod.stock_quantity < ci.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient inventory for '{prod.title}'. Requested: {ci.quantity}, Available: {prod.stock_quantity}"
            )
        
        shop_id = prod.shop_id
        if shop_id not in items_by_shop:
            items_by_shop[shop_id] = []
        items_by_shop[shop_id].append((ci, prod))

    # Resolve delivery fee based on delivery area or default
    delivery_fee = Decimal(str(settings.DEFAULT_DELIVERY_FEE))
    area = db.query(DeliveryArea).filter(
        DeliveryArea.city.ilike(data.delivery_city.strip()),
        DeliveryArea.is_active == True
    ).first()
    if area:
        delivery_fee = Decimal(str(area.delivery_fee))

    # Calculate subtotal and build order inside a transaction
    total_subtotal = Decimal("0.00")
    order_number = f"GBM-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"

    order = Order(
        order_number=order_number,
        customer_id=current_user.id,
        customer_name=data.delivery_name.strip(),
        customer_phone=data.delivery_phone.strip(),
        customer_email=current_user.email,
        delivery_city=data.delivery_city.strip(),
        delivery_locality=data.delivery_locality.strip(),
        delivery_address=data.delivery_address.strip(),
        delivery_landmark=data.delivery_landmark.strip() if data.delivery_landmark else None,
        customer_notes=data.customer_notes,
        subtotal=Decimal("0.00"),
        delivery_fee=delivery_fee,
        total_amount=Decimal("0.00"),
        payment_method="Cash on Delivery",
        payment_status="Pending",
        status=OrderStatus.PENDING_CONFIRMATION.value
    )
    db.add(order)
    db.flush()  # to obtain order.id

    # Create per-shop groups and order items, and decrement stock
    for shop_id, group_items in items_by_shop.items():
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        comm_rate = shop.commission_rate if shop.commission_rate is not None else settings.MARKETPLACE_COMMISSION_PERCENT
        comm_rate_dec = Decimal(str(comm_rate)) / Decimal("100.0")

        shop_subtotal = Decimal("0.00")

        shop_group = ShopOrderGroup(
            order_id=order.id,
            shop_id=shop_id,
            subtotal=Decimal("0.00"),
            commission_rate=float(comm_rate),
            commission_amount=Decimal("0.00"),
            seller_payout=Decimal("0.00"),
            status=OrderStatus.PENDING_CONFIRMATION.value
        )
        db.add(shop_group)
        db.flush()

        for ci, prod in group_items:
            unit_price = Decimal(str(prod.price))
            item_sub = unit_price * Decimal(str(ci.quantity))
            shop_subtotal += item_sub

            # Primary image
            img_url = prod.images[0].image_url if prod.images else None

            order_item = OrderItem(
                order_id=order.id,
                shop_order_group_id=shop_group.id,
                product_id=prod.id,
                product_title=prod.title,
                product_image=img_url,
                unit_price=unit_price,
                quantity=ci.quantity,
                subtotal=item_sub
            )
            db.add(order_item)

            # Atomic stock decrement
            prod.stock_quantity -= ci.quantity
            if prod.stock_quantity == 0:
                prod.status = ProductStatus.OUT_OF_STOCK.value

        comm_amount = (shop_subtotal * comm_rate_dec).quantize(Decimal("0.01"))
        seller_payout = shop_subtotal - comm_amount

        shop_group.subtotal = shop_subtotal
        shop_group.commission_amount = comm_amount
        shop_group.seller_payout = seller_payout
        total_subtotal += shop_subtotal

        # Auto-create Delivery record for this shop group
        delivery = Delivery(
            order_id=order.id,
            shop_order_group_id=shop_group.id,
            pickup_address=f"{shop.name}, {shop.address}, {shop.locality}, {shop.city} (Phone: {shop.phone})",
            delivery_address=f"{order.customer_name}, {order.delivery_address}, {order.delivery_locality}, {order.delivery_city} (Phone: {order.customer_phone})",
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            status="Pending Assignment"
        )
        db.add(delivery)

    order.subtotal = total_subtotal
    order.total_amount = total_subtotal + delivery_fee

    # Record initial status history
    history = OrderStatusHistory(
        order_id=order.id,
        previous_status=None,
        new_status=OrderStatus.PENDING_CONFIRMATION.value,
        changed_by_id=current_user.id,
        changed_by_role=current_user.role,
        notes="Order placed by customer via Cash on Delivery"
    )
    db.add(history)

    # Clear customer's cart
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

    db.commit()
    db.refresh(order)

    record_audit(
        db=db,
        actor=current_user,
        action="ORDER_CHECKOUT",
        entity_type="Order",
        entity_id=str(order.id),
        details=f"Order {order.order_number} placed. Total: PKR {order.total_amount}",
        request=request
    )

    return _format_order(order)

@router.get("/my-orders")
def list_customer_orders(
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
) -> Any:
    """Customer: View list of their own orders."""
    orders = db.query(Order).filter(Order.customer_id == current_user.id).order_by(Order.created_at.desc()).all()
    return [_format_order(o) for o in orders]

@router.get("/{order_id}")
def get_order_detail(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """View details of an order. Strict authorization: Customer can only view own order; Shopkeeper only if their shop has items; Admin can view all."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role == UserRole.ADMIN.value:
        return _format_order(order)
    
    if current_user.role == UserRole.CUSTOMER.value and order.customer_id == current_user.id:
        return _format_order(order)

    if current_user.role == UserRole.SHOPKEEPER.value:
        # Check if shopkeeper owns any shop in this order
        shop_ids = [sg.shop.owner_id for sg in order.shop_groups if sg.shop]
        if current_user.id in shop_ids or order.customer_id == current_user.id:
            return _format_order(order)

    raise HTTPException(status_code=403, detail="Access denied: You are not authorized to view this order")

# ----------------- Seller Orders -----------------

@router.get("/seller/my-orders")
def list_seller_orders(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_shopkeeper),
    db: Session = Depends(get_db)
) -> Any:
    """Shopkeeper: View fulfillment order groups for their shop."""
    shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if not shop:
        raise HTTPException(status_code=400, detail="You do not have a registered shop")

    query = db.query(ShopOrderGroup).filter(ShopOrderGroup.shop_id == shop.id)
    if status_filter:
        query = query.filter(ShopOrderGroup.status == status_filter)
    groups = query.order_by(ShopOrderGroup.created_at.desc()).all()

    return [
        {
            "id": g.id,
            "order_id": g.order_id,
            "order_number": g.order.order_number if g.order else "",
            "customer_name": g.order.customer_name if g.order else "",
            "customer_phone": g.order.customer_phone if g.order else "",
            "delivery_address": f"{g.order.delivery_address}, {g.order.delivery_locality}, {g.order.delivery_city}" if g.order else "",
            "subtotal": float(g.subtotal),
            "commission_amount": float(g.commission_amount),
            "seller_payout": float(g.seller_payout),
            "status": g.status,
            "cancellation_reason": g.cancellation_reason,
            "created_at": g.created_at,
            "items": [
                {
                    "id": item.id,
                    "product_title": item.product_title,
                    "product_image": item.product_image,
                    "unit_price": float(item.unit_price),
                    "quantity": item.quantity,
                    "subtotal": float(item.subtotal)
                }
                for item in g.items
            ]
        }
        for g in groups
    ]

@router.put("/seller/order-groups/{group_id}/status")
def update_seller_order_status(
    group_id: int,
    data: OrderStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_shopkeeper),
    db: Session = Depends(get_db)
) -> Any:
    """Shopkeeper: Update fulfillment status of an order group (Confirmed, Preparing, Packed, Ready for Pickup)."""
    shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if not shop:
        raise HTTPException(status_code=400, detail="You do not have a registered shop")

    group = db.query(ShopOrderGroup).filter(
        ShopOrderGroup.id == group_id,
        ShopOrderGroup.shop_id == shop.id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Order group not found or not owned by your shop")

    # Permitted shopkeeper status updates
    permitted_statuses = [
        OrderStatus.CONFIRMED.value,
        OrderStatus.PREPARING.value,
        OrderStatus.PACKED.value,
        OrderStatus.READY_FOR_PICKUP.value
    ]
    if data.status not in permitted_statuses and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=400, detail=f"Shopkeepers can only transition status to: {permitted_statuses}")

    prev_status = group.status
    group.status = data.status

    # Record history
    history = OrderStatusHistory(
        order_id=group.order_id,
        shop_order_group_id=group.id,
        previous_status=prev_status,
        new_status=data.status,
        changed_by_id=current_user.id,
        changed_by_role=current_user.role,
        notes=data.notes or f"Shop '{shop.name}' updated status to {data.status}"
    )
    db.add(history)

    # Check if all shop groups have reached at least this status, update overall order if appropriate
    order = group.order
    all_statuses = [sg.status for sg in order.shop_groups]
    if all(s == OrderStatus.CONFIRMED.value for s in all_statuses):
        order.status = OrderStatus.CONFIRMED.value
    elif any(s in [OrderStatus.PREPARING.value, OrderStatus.PACKED.value] for s in all_statuses):
        order.status = OrderStatus.PREPARING.value

    db.commit()
    db.refresh(group)
    return {"message": "Status updated successfully", "status": group.status}

# ----------------- Order Cancellations -----------------

@router.post("/cancel-request", status_code=status.HTTP_201_CREATED)
def request_order_cancellation(
    data: CancellationRequestCreate,
    request: Request,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
) -> Any:
    """Customer: Request cancellation for an order they own before terminal/dispatch state."""
    order = db.query(Order).filter(Order.id == data.order_id, Order.customer_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or does not belong to you")

    terminal_statuses = [
        OrderStatus.DELIVERED.value,
        OrderStatus.OUT_FOR_DELIVERY.value,
        OrderStatus.CANCELLED.value
    ]
    if order.status in terminal_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order in '{order.status}' status. Please contact customer support."
        )

    # Automatic cancellation if still Pending Confirmation
    if order.status == OrderStatus.PENDING_CONFIRMATION.value:
        order.status = OrderStatus.CANCELLED.value
        order.cancellation_reason = data.reason

        # Release stock back to products
        for item in order.items:
            if item.product:
                item.product.stock_quantity += item.quantity
                if item.product.status == ProductStatus.OUT_OF_STOCK.value:
                    item.product.status = ProductStatus.ACTIVE.value

        # Update all groups
        for sg in order.shop_groups:
            sg.status = OrderStatus.CANCELLED.value
            sg.cancellation_reason = data.reason

        history = OrderStatusHistory(
            order_id=order.id,
            previous_status=OrderStatus.PENDING_CONFIRMATION.value,
            new_status=OrderStatus.CANCELLED.value,
            changed_by_id=current_user.id,
            changed_by_role=current_user.role,
            notes=f"Order auto-cancelled by customer before confirmation: {data.reason}"
        )
        db.add(history)

        cancel_req = CancellationRequest(
            order_id=order.id,
            shop_order_group_id=data.shop_order_group_id,
            requested_by_id=current_user.id,
            reason=data.reason,
            status=CancellationStatus.APPROVED.value,
            admin_notes="Auto-approved prior to merchant confirmation"
        )
        db.add(cancel_req)
        db.commit()
        return {"message": "Order cancelled successfully and stock restored"}

    # If already confirmed or preparing, record cancellation request for admin/seller review
    cancel_req = CancellationRequest(
        order_id=order.id,
        shop_order_group_id=data.shop_order_group_id,
        requested_by_id=current_user.id,
        reason=data.reason,
        status=CancellationStatus.PENDING.value
    )
    order.status = OrderStatus.CANCELLATION_REQUESTED.value
    db.add(cancel_req)

    history = OrderStatusHistory(
        order_id=order.id,
        previous_status=order.status,
        new_status=OrderStatus.CANCELLATION_REQUESTED.value,
        changed_by_id=current_user.id,
        changed_by_role=current_user.role,
        notes=f"Cancellation requested by customer: {data.reason}"
    )
    db.add(history)
    db.commit()
    return {"message": "Cancellation request submitted for review"}
