from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
import bcrypt
import jwt
from backend.app.core.config import settings

# Argon2id password hasher
_ph = PasswordHasher()

def hash_password(password: str) -> str:
    """Hashes a password using Argon2id."""
    return _ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against an Argon2id or bcrypt hash."""
    if not hashed_password or not plain_password:
        return False
    
    # Check if Argon2 hash
    if hashed_password.startswith("$argon2"):
        try:
            return _ph.verify(hashed_password, plain_password)
        except (VerifyMismatchError, VerificationError):
            return False
        except Exception:
            return False
    
    # Check if bcrypt hash
    if hashed_password.startswith("$2a$") or hashed_password.startswith("$2b$"):
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    return False

def create_access_token(
    subject: Union[str, Any],
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Creates a signed JWT access token with role and expiration."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": now,
        "nbf": now
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None
