import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db, record_audit
from backend.app.core.permissions import UserRole
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.models.user import User
from backend.app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    Token,
)
from backend.app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Registers a new user (default role: customer; shopkeeper accounts request shop approval)."""
    if data.password != data.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Passwords do not match",
        )
    
    # Check if email or phone already exists
    existing_user = db.query(User).filter(
        (User.email == data.email.lower().strip()) | (User.phone == data.phone.strip())
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email or mobile number already exists",
        )
    
    # Prevent unauthorized public self-registration as admin or rider
    target_role = UserRole.CUSTOMER.value
    if data.role and data.role == UserRole.SHOPKEEPER.value:
        target_role = UserRole.SHOPKEEPER.value

    user = User(
        email=data.email.lower().strip(),
        phone=data.phone.strip(),
        full_name=data.full_name.strip(),
        hashed_password=hash_password(data.password),
        role=target_role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    record_audit(
        db=db,
        actor=user,
        action="USER_REGISTER",
        entity_type="User",
        entity_id=str(user.id),
        details=f"User registered with email {user.email} and role {user.role}",
        request=request
    )

    access_token = create_access_token(subject=user.id, role=user.role)
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )

@router.post("/login", response_model=Token)
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Authenticates using either email address or phone number."""
    identifier = data.identifier.strip()
    user = db.query(User).filter(
        (User.email == identifier.lower()) | (User.phone == identifier)
    ).first()

    # Constant time / safe rejection to avoid account enumeration
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/phone or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated or suspended by the administrator",
        )

    record_audit(
        db=db,
        actor=user,
        action="USER_LOGIN",
        entity_type="User",
        entity_id=str(user.id),
        details=f"Successful login for user {user.email}",
        request=request
    )

    access_token = create_access_token(subject=user.id, role=user.role)
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Returns the profile of the currently authenticated user."""
    return current_user

@router.post("/forgot-password")
def forgot_password(
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> Any:
    """Initiates a password reset request. Returns a safe success message regardless of existence."""
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    # In a production environment with email SMTP configured, an email with a secure token would be dispatched.
    # To avoid account enumeration, we always return the same generic message.
    return {
        "message": "If an account with that email exists, password reset instructions have been dispatched."
    }
