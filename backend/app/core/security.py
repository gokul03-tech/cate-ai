"""
LexOrch-KG — Security Utilities
JWT token creation/verification, password hashing, and RBAC helpers.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing context (bcrypt)
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compare plain text password against stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    return pwd_context.hash(password)


# ---------------------------------------------------------------------------
# JWT Token helpers
# ---------------------------------------------------------------------------

def create_access_token(
    subject: str | UUID,
    role: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a short-lived access token.

    Args:
        subject: User ID (UUID or string)
        role: User role (admin, judge, lawyer, analyst)
        extra_claims: Additional claims to embed in the token
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(subject: str | UUID) -> str:
    """Create a long-lived refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e


def verify_access_token(token: str) -> dict[str, Any]:
    """Verify token is an access token and return payload."""
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise ValueError("Token is not an access token")
    return payload


def verify_refresh_token(token: str) -> dict[str, Any]:
    """Verify token is a refresh token and return payload."""
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise ValueError("Token is not a refresh token")
    return payload
