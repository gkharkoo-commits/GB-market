import re
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_current_admin,
    get_current_shopkeeper,
    get_db,
)
from backend.app.core.permissions import ProductStatus, ShopVerificationStatus, UserRole
from backend.app.models.category import Category
from backend.app.models.product import Product, ProductImage
from backend.app.models.shop import Shop
from backend.app.models.user import User
from backend.app.schemas.product import (
    ProductCreate,
    ProductImageResponse,
    ProductResponse,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["Products"])

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s

def _format_product_response(product: Product) -> dict:
    """Helper to convert product model with relations into response dict."""
    return {
        "id": product.id,
        "shop_id": product.shop_id,
        "category_id": product.category_id,
        "title": product.title,
        "slug": product.slug,
        "description": product.description,
        "price": float(product.price),
        "original_price": float(product.original_price) if product.original_price else None,
        "stock_quantity": product.stock_quantity,
        "status": product.status,
        "unit": product.unit,
        "is_featured": product.is_featured,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "shop_name": product.shop.name if product.shop else None,
        "category_name": product.category.name if product.category else None,
        "images": [
            {
                "id": img.id,
                "product_id": img.product_id,
                "image_url": img.image_url,
                "is_primary": img.is_primary,
                "display_order": img.display_order,
                "created_at": img.created_at
            }
            for img in product.images
        ]
    }

@router.get("/")
def list_products(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    shop_id: Optional[int] = None,
    city: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = False,
    is_featured: Optional[bool] = None,
    sort_by: str = "newest",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Any:
    """Public: Search, filter, and paginate products across Gilgit-Baltistan."""
    # Only show active products from approved, active shops
    query = db.query(Product).join(Shop, Product.shop_id == Shop.id).filter(
        Product.status == ProductStatus.ACTIVE.value,
        Shop.verification_status == ShopVerificationStatus.APPROVED.value,
        Shop.is_active == True
    )

    if search:
        query = query.filter(
            (Product.title.ilike(f"%{search}%")) |
            (Product.description.ilike(f"%{search}%")) |
            (Shop.name.ilike(f"%{search}%"))
        )
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if shop_id:
        query = query.filter(Product.shop_id == shop_id)
    if city:
        query = query.filter(Shop.city.ilike(f"%{city}%"))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if in_stock_only:
        query = query.filter(Product.stock_quantity > 0)
    if is_featured is not None:
        query = query.filter(Product.is_featured == is_featured)

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    total = query.count()
    offset = (page - 1) * limit
    products = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [_format_product_response(p) for p in products]
    }

@router.get("/detail/{slug}")
def get_product_by_slug(
    slug: str,
    db: Session = Depends(get_db)
) -> Any:
    """Public: View full product details with shop information and image gallery."""
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Verify shop is approved
    if product.shop.verification_status != ShopVerificationStatus.APPROVED.value or not product.shop.is_active:
        raise HTTPException(status_code=404, detail="Product is not currently available")

    return _format_product_response(product)

# ----------------- Shopkeeper Products Management -----------------

@router.get("/seller/my-products")
def list_my_products(
    current_user: User = Depends(get_current_shopkeeper),
    db: Session = Depends(get_db)
) -> Any:
    """Shopkeeper: List all products in their own shop."""
    shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if not shop:
        raise HTTPException(status_code=400, detail="You do not have a registered shop")
    
    products = db.query(Product).filter(Product.shop_id == shop.id).order_by(Product.created_at.desc()).all()
    return [_format_product_response(p) for p in products]

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    current_user: User = Depends(get_current_shopkeeper),
    db: Session = Depends(get_db)
) -> Any:
    """Shopkeeper: Add a new product to their approved shop."""
    shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if not shop:
        raise HTTPException(status_code=400, detail="You do not have a registered shop")
    
    # Requirement: "A shopkeeper must not sell until the shop is approved by the administrator."
    if shop.verification_status != ShopVerificationStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot add products. Shop verification status is '{shop.verification_status}'. Only approved shops can sell."
        )

    # Generate unique product slug
    base_slug = slugify(data.title)
    slug = f"{shop.slug}-{base_slug}"
    counter = 1
    while db.query(Product).filter(Product.slug == slug).first():
        slug = f"{shop.slug}-{base_slug}-{counter}"
        counter += 1

    product = Product(
        shop_id=shop.id,
        category_id=data.category_id,
        title=data.title.strip(),
        slug=slug,
        description=data.description.strip(),
        price=data.price,
        original_price=data.original_price,
        stock_quantity=data.stock_quantity,
        unit=data.unit,
        is_featured=data.is_featured,
        status=ProductStatus.ACTIVE.value if data.stock_quantity > 0 else ProductStatus.OUT_OF_STOCK.value
    )
    db.add(product)
    db.flush()  # to obtain product.id

    # Add images
    for idx, url in enumerate(data.image_urls):
        img = ProductImage(
            product_id=product.id,
            image_url=url,
            is_primary=(idx == 0),
            display_order=idx
        )
        db.add(img)

    db.commit()
    db.refresh(product)
    return _format_product_response(product)

@router.put("/{product_id}")
def update_product(
    product_id: int,
    data: ProductUpdate,
    current_user: User = Depends(get_current_shopkeeper),
    db: Session = Depends(get_db)
) -> Any:
    """Shopkeeper: Update a product in their own shop."""
    shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if not shop:
        raise HTTPException(status_code=400, detail="You do not have a registered shop")
    
    product = db.query(Product).filter(Product.id == product_id, Product.shop_id == shop.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or does not belong to your shop")

    if data.title:
        product.title = data.title.strip()
    if data.category_id is not None:
        product.category_id = data.category_id
    if data.description:
        product.description = data.description.strip()
    if data.price is not None:
        product.price = data.price
    if data.original_price is not None:
        product.original_price = data.original_price
    if data.stock_quantity is not None:
        product.stock_quantity = data.stock_quantity
        if product.stock_quantity == 0 and product.status == ProductStatus.ACTIVE.value:
            product.status = ProductStatus.OUT_OF_STOCK.value
        elif product.stock_quantity > 0 and product.status == ProductStatus.OUT_OF_STOCK.value:
            product.status = ProductStatus.ACTIVE.value
    if data.status:
        product.status = data.status
    if data.unit:
        product.unit = data.unit
    if data.is_featured is not None:
        product.is_featured = data.is_featured

    db.commit()
    db.refresh(product)
    return _format_product_response(product)

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_shopkeeper),
    db: Session = Depends(get_db)
) -> Any:
    """Shopkeeper: Remove/archive a product."""
    shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if not shop:
        raise HTTPException(status_code=400, detail="You do not have a registered shop")
    
    product = db.query(Product).filter(Product.id == product_id, Product.shop_id == shop.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or does not belong to your shop")

    db.delete(product)
    db.commit()
    return {"message": "Product removed successfully"}
