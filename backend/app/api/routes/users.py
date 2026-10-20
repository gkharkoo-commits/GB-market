from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.security import hash_password, verify_password
from backend.app.models.user import Address, User
from backend.app.schemas.user import (
    AddressCreate,
    AddressResponse,
    UserDetailResponse,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Users & Addresses"])

@router.get("/profile", response_model=UserDetailResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Returns the authenticated user's profile and saved delivery addresses."""
    addresses = db.query(Address).filter(Address.user_id == current_user.id).all()
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "phone": current_user.phone,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "profile_image": current_user.profile_image,
        "created_at": current_user.created_at,
        "addresses": addresses
    }
    return user_dict

@router.put("/profile", response_model=UserResponse)
def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Updates basic profile info."""
    if data.full_name:
        current_user.full_name = data.full_name.strip()
    if data.phone:
        # Check if phone in use by someone else
        existing = db.query(User).filter(User.phone == data.phone.strip(), User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="This phone number is already registered by another account")
        current_user.phone = data.phone.strip()
    if data.profile_image is not None:
        current_user.profile_image = data.profile_image

    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/change-password")
def change_password(
    data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Safely updates user password after validating current password."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    
    if data.new_password != data.new_password_confirm:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="New passwords do not match")

    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

# ----------------- Addresses -----------------

@router.get("/addresses", response_model=List[AddressResponse])
def list_addresses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Returns the user's saved addresses."""
    return db.query(Address).filter(Address.user_id == current_user.id).all()

@router.post("/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(
    data: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Adds a new delivery address."""
    if data.is_default:
        # Clear existing default
        db.query(Address).filter(Address.user_id == current_user.id).update({"is_default": False})

    address = Address(
        user_id=current_user.id,
        title=data.title,
        full_name=data.full_name,
        phone=data.phone,
        city=data.city,
        locality=data.locality,
        address_line=data.address_line,
        landmark=data.landmark,
        is_default=data.is_default
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address

@router.delete("/addresses/{address_id}")
def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Deletes an address belonging strictly to the current user."""
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == current_user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    
    db.delete(address)
    db.commit()
    return {"message": "Address deleted"}
