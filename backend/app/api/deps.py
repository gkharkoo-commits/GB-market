from typing import Generator, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.permissions import UserRole
from backend.app.core.security import decode_access_token
from backend.app.db.session import SessionLocal, get_db
from backend.app.models.audit import AuditLog
from backend.app.models.user import User

security_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Authenticates the user from JWT bearer token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or malformed authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account does not exist or has been removed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated or suspended",
        )
    
    return user

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Returns the current user if a valid token is provided, or None for guest visitors."""
    if not credentials:
        return None
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None

def get_current_customer(current_user: User = Depends(get_current_user)) -> User:
    """Ensures user is an active customer (or higher role)."""
    return current_user

def get_current_shopkeeper(current_user: User = Depends(get_current_user)) -> User:
    """Ensures user has shopkeeper or admin privileges."""
    if current_user.role not in [UserRole.SHOPKEEPER.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: shopkeeper or administrator privileges required",
        )
    return current_user

def get_current_rider(current_user: User = Depends(get_current_user)) -> User:
    """Ensures user has rider or admin privileges."""
    if current_user.role not in [UserRole.RIDER.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: delivery rider or administrator privileges required",
        )
    return current_user

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensures user has administrator privileges."""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: administrator privileges required",
        )
    return current_user

def record_audit(
    db: Session,
    actor: Optional[User],
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    details: Optional[str] = None,
    request: Optional[Request] = None
):
    """Safely logs an administrative or security-sensitive audit event."""
    ip_address = None
    if request and request.client:
        ip_address = request.client.host

    audit = AuditLog(
        actor_id=actor.id if actor else None,
        actor_email=actor.email if actor else "anonymous",
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        details=details,
        ip_address=ip_address
    )
    db.add(audit)
    db.commit()
