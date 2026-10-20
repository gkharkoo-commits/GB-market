from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import re

from backend.app.api.deps import get_current_admin, get_db
from backend.app.models.category import Category
from backend.app.models.user import User
from backend.app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["Categories"])

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s

@router.get("/", response_model=List[CategoryResponse])
def list_categories(
    active_only: bool = True,
    db: Session = Depends(get_db)
) -> Any:
    """Returns product categories."""
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active == True)
    return query.order_by(Category.display_order.asc(), Category.name.asc()).all()

@router.get("/{slug}", response_model=CategoryResponse)
def get_category_by_slug(
    slug: str,
    db: Session = Depends(get_db)
) -> Any:
    """Returns single category details by slug."""
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: Create a new marketplace category."""
    existing = db.query(Category).filter(
        (Category.name.ilike(data.name.strip())) | (Category.slug == data.slug.strip())
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name or slug already exists")
    
    cat = Category(
        name=data.name.strip(),
        slug=slugify(data.slug or data.name),
        description=data.description,
        image_url=data.image_url,
        icon=data.icon,
        is_active=data.is_active,
        display_order=data.display_order
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: Update a marketplace category."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if data.name:
        cat.name = data.name.strip()
    if data.slug:
        cat.slug = slugify(data.slug)
    if data.description is not None:
        cat.description = data.description
    if data.image_url is not None:
        cat.image_url = data.image_url
    if data.icon is not None:
        cat.icon = data.icon
    if data.is_active is not None:
        cat.is_active = data.is_active
    if data.display_order is not None:
        cat.display_order = data.display_order

    db.commit()
    db.refresh(cat)
    return cat
