"""
LexOrch-KG — FastAPI Dependencies
JWT authentication, role-based access, and current user injection.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_access_token
from app.infrastructure.postgres.models import User
from app.repositories.repositories import UserRepository

# HTTP Bearer token extractor
security = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Extract and validate JWT token, return the authenticated User.
    
    Raises:
        HTTPException 401: Invalid or expired token
        HTTPException 404: User not found
        HTTPException 403: Account inactive
    """
    token = credentials.credentials

    try:
        payload = verify_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Missing user ID in token")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return user


def require_roles(*roles: str):
    """
    Role-based access control decorator factory.
    
    Usage:
        @router.get("/admin", dependencies=[Depends(require_roles("admin"))])
    """
    async def _check_role(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' is not authorized for this action. Required: {list(roles)}",
            )
        return current_user
    return _check_role


# Convenience dependencies
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminOnly = Depends(require_roles("admin"))
JudgeOrAdmin = Depends(require_roles("admin", "judge"))
LawyerOrAbove = Depends(require_roles("admin", "judge", "lawyer"))
