import re
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_current_admin,
    get_current_customer,
    get_current_shopkeeper,
    get_current_user,
    get_db,
    record_audit,
)
from backend.app.core.permissions import ShopVerificationStatus, UserRole
from backend.app.models.category import Category
from backend.app.models.shop import Shop, ShopVerificationDoc
from backend.app.models.user import User
from backend.app.schemas.shop import (
    ShopAdminReview,
    ShopCreate,
    ShopPublicSummary,
    ShopResponse,
    ShopUpdate,
    ShopVerificationDocResponse,
)

router = APIRouter(prefix="/shops", tags=["Shops"])

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s

@router.get("/", response_model=List[ShopPublicSummary])
def list_approved_shops(
    city: Optional[str] = None,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> Any:
    """Public: Browse approved and active shops in Gilgit-Baltistan."""
    query = db.query(Shop).filter(
        Shop.verification_status == ShopVerificationStatus.APPROVED.value,
        Shop.is_active == True
    )
    if city:
        query = query.filter(Shop.city.ilike(f"%{city}%"))
    if category_id:
        query = query.filter(Shop.category_id == category_id)
    if search:
        query = query.filter(
            (Shop.name.ilike(f"%{search}%")) | (Shop.description.ilike(f"%{search}%"))
        )
    return query.limit(limit).all()

@router.get("/detail/{slug}", response_model=ShopResponse)
def get_shop_by_slug(
    slug: str,
    db: Session = Depends(get_db)
) -> Any:
    """Public: View detailed profile of an approved shop."""
    shop = db.query(Shop).filter(Shop.slug == slug).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Non-admins can only see approved shops publicly
    if shop.verification_status != ShopVerificationStatus.APPROVED.value and not shop.is_active:
        raise HTTPException(status_code=404, detail="Shop is currently not accessible")
    return shop

@router.get("/my-shop", response_model=Optional[ShopResponse])
def get_my_shop(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Shopkeeper: View status and details of their registered shop."""
    shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    return shop

@router.post("/register", response_model=ShopResponse, status_code=status.HTTP_201_CREATED)
def register_shop(
    data: ShopCreate,
    request: Request,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
) -> Any:
    """Customer: Apply for shopkeeper vendor registration. Status is set to Pending."""
    existing_shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if existing_shop:
        raise HTTPException(
            status_code=400,
            detail=f"You already have a registered shop '{existing_shop.name}' with status: {existing_shop.verification_status}"
        )

    # Generate unique slug
    base_slug = slugify(data.name)
    slug = base_slug
    counter = 1
    while db.query(Shop).filter(Shop.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    shop = Shop(
        owner_id=current_user.id,
        category_id=data.category_id,
        name=data.name.strip(),
        slug=slug,
        owner_name=data.owner_name.strip(),
        phone=data.phone.strip(),
        city=data.city.strip(),
        locality=data.locality.strip(),
        address=data.address.strip(),
        landmark=data.landmark,
        description=data.description.strip(),
        opening_hours=data.opening_hours,
        available_delivery_methods=data.available_delivery_methods,
        exterior_image=data.exterior_image,
        interior_image=data.interior_image,
        owner_image=data.owner_image,
        verification_status=ShopVerificationStatus.PENDING.value,
        is_active=True
    )
    db.add(shop)

    # Promote user role to shopkeeper if currently customer
    if current_user.role == UserRole.CUSTOMER.value:
        current_user.role = UserRole.SHOPKEEPER.value

    db.commit()
    db.refresh(shop)

    record_audit(
        db=db,
        actor=current_user,
        action="SHOP_REGISTER_SUBMIT",
        entity_type="Shop",
        entity_id=str(shop.id),
        details=f"New shop registration submitted: {shop.name} in {shop.city}",
        request=request
    )
    return shop

@router.put("/my-shop", response_model=ShopResponse)
def update_my_shop(
    data: ShopUpdate,
    current_user: User = Depends(get_current_shopkeeper),
    db: Session = Depends(get_db)
) -> Any:
    """Shopkeeper: Update profile of own shop."""
    shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="No shop found for your account")
    
    if data.name:
        shop.name = data.name.strip()
    if data.category_id is not None:
        shop.category_id = data.category_id
    if data.phone:
        shop.phone = data.phone.strip()
    if data.city:
        shop.city = data.city.strip()
    if data.locality:
        shop.locality = data.locality.strip()
    if data.address:
        shop.address = data.address.strip()
    if data.landmark is not None:
        shop.landmark = data.landmark
    if data.description:
        shop.description = data.description.strip()
    if data.opening_hours:
        shop.opening_hours = data.opening_hours
    if data.available_delivery_methods:
        shop.available_delivery_methods = data.available_delivery_methods
    if data.exterior_image:
        shop.exterior_image = data.exterior_image
    if data.interior_image is not None:
        shop.interior_image = data.interior_image
    if data.owner_image is not None:
        shop.owner_image = data.owner_image

    db.commit()
    db.refresh(shop)
    return shop

# ----------------- Admin Review Endpoints -----------------

@router.get("/admin/applications", response_model=List[ShopResponse])
def list_shop_applications_admin(
    status_filter: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: List all shop applications with filtering (pending, approved, rejected, suspended)."""
    query = db.query(Shop)
    if status_filter:
        query = query.filter(Shop.verification_status == status_filter.lower())
    return query.order_by(Shop.created_at.desc()).all()

@router.put("/admin/{shop_id}/review", response_model=ShopResponse)
def review_shop_admin(
    shop_id: int,
    data: ShopAdminReview,
    request: Request,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: Approve, Reject, or Suspend a shop registration."""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    valid_statuses = [
        ShopVerificationStatus.APPROVED.value,
        ShopVerificationStatus.REJECTED.value,
        ShopVerificationStatus.SUSPENDED.value,
        ShopVerificationStatus.PENDING.value,
    ]
    if data.status.lower() not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    shop.verification_status = data.status.lower()
    if data.verification_notes is not None:
        shop.verification_notes = data.verification_notes
    if data.commission_rate is not None:
        shop.commission_rate = data.commission_rate

    db.commit()
    db.refresh(shop)

    record_audit(
        db=db,
        actor=current_admin,
        action="SHOP_ADMIN_REVIEW",
        entity_type="Shop",
        entity_id=str(shop.id),
        details=f"Shop '{shop.name}' review decision: {shop.verification_status}. Notes: {shop.verification_notes}",
        request=request
    )
    return shop
