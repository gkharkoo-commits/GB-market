from typing import Any, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from backend.app.api.deps import get_db, get_optional_current_user
from backend.app.core.permissions import ProductStatus, ShopVerificationStatus
from backend.app.models.cart import Cart, CartItem
from backend.app.models.product import Product
from backend.app.models.shop import Shop
from backend.app.models.user import User
from backend.app.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse

router = APIRouter(prefix="/cart", tags=["Cart"])

def _get_or_create_cart(
    db: Session,
    user: Optional[User],
    session_id: Optional[str]
) -> Cart:
    """Finds or creates a cart matching either the authenticated user or guest session id."""
    cart = None
    if user:
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            cart = Cart(user_id=user.id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
        return cart

    # Guest user with session_id
    if not session_id:
        session_id = str(uuid.uuid4())
    
    cart = db.query(Cart).filter(Cart.session_id == session_id).first()
    if not cart:
        cart = Cart(session_id=session_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

def _format_cart(cart: Cart) -> dict:
    items_out = []
    subtotal = 0.0
    total_items = 0

    for item in cart.items:
        prod = item.product
        if not prod:
            continue
        
        # Primary image
        img_url = None
        if prod.images:
            img_url = prod.images[0].image_url

        unit_p = float(prod.price)
        item_sub = unit_p * item.quantity
        subtotal += item_sub
        total_items += item.quantity

        items_out.append({
            "id": item.id,
            "product_id": prod.id,
            "quantity": item.quantity,
            "product_title": prod.title,
            "product_price": unit_p,
            "product_image": img_url,
            "shop_id": prod.shop_id,
            "shop_name": prod.shop.name if prod.shop else "Shop",
            "available_stock": prod.stock_quantity,
            "subtotal": round(item_sub, 2)
        })

    return {
        "id": cart.id,
        "total_items": total_items,
        "subtotal": round(subtotal, 2),
        "items": items_out
    }

@router.get("/")
def get_cart(
    x_session_id: Optional[str] = Header(None),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Returns the current contents, prices, and stock of the shopping cart."""
    cart = _get_or_create_cart(db, current_user, x_session_id)
    return _format_cart(cart)

@router.post("/items", status_code=status.HTTP_200_OK)
def add_to_cart(
    data: CartItemCreate,
    x_session_id: Optional[str] = Header(None),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Adds a product to the cart with backend stock verification."""
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product or product.status != ProductStatus.ACTIVE.value:
        raise HTTPException(status_code=404, detail="Product not available for purchase")
    
    if product.shop.verification_status != ShopVerificationStatus.APPROVED.value or not product.shop.is_active:
        raise HTTPException(status_code=400, detail="Shop is not approved to sell")

    if product.stock_quantity < data.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Requested quantity ({data.quantity}) exceeds available stock ({product.stock_quantity})"
        )

    cart = _get_or_create_cart(db, current_user, x_session_id)
    cart_item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == product.id).first()

    if cart_item:
        new_qty = cart_item.quantity + data.quantity
        if product.stock_quantity < new_qty:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot add more. Total in cart ({new_qty}) exceeds stock ({product.stock_quantity})"
            )
        cart_item.quantity = new_qty
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=data.quantity
        )
        db.add(cart_item)

    db.commit()
    db.refresh(cart)
    return _format_cart(cart)

@router.put("/items/{item_id}")
def update_cart_item(
    item_id: int,
    data: CartItemUpdate,
    x_session_id: Optional[str] = Header(None),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Updates the quantity of an item in the cart."""
    cart = _get_or_create_cart(db, current_user, x_session_id)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in your cart")

    if item.product.stock_quantity < data.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Requested quantity ({data.quantity}) exceeds available stock ({item.product.stock_quantity})"
        )

    item.quantity = data.quantity
    db.commit()
    db.refresh(cart)
    return _format_cart(cart)

@router.delete("/items/{item_id}")
def remove_from_cart(
    item_id: int,
    x_session_id: Optional[str] = Header(None),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Removes an item from the cart."""
    cart = _get_or_create_cart(db, current_user, x_session_id)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in your cart")

    db.delete(item)
    db.commit()
    db.refresh(cart)
    return _format_cart(cart)

@router.delete("/clear")
def clear_cart(
    x_session_id: Optional[str] = Header(None),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Clears all items in the cart."""
    cart = _get_or_create_cart(db, current_user, x_session_id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    db.refresh(cart)
    return _format_cart(cart)
