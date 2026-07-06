"""
LexOrch-KG — Auth API Router
Endpoints: register, login, refresh, logout, me
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.core.database import get_db
from app.schemas.schemas import (
    RefreshTokenRequest,
    TokenResponse,
    UserRead,
    UserRegister,
    UserLogin,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    data: UserRegister,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create a new user account.
    
    - **email**: Unique email address
    - **password**: Min 8 chars, must include uppercase and digit
    - **role**: analyst (default) | lawyer | judge | admin
    """
    service = AuthService(db)
    try:
        user = await service.register(
            data, ip_address=request.client.host if request.client else None
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get JWT tokens",
)
async def login(
    data: UserLogin,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Authenticate and receive access + refresh tokens.
    
    Access token expires in 30 minutes.
    Refresh token expires in 7 days.
    """
    service = AuthService(db)
    try:
        tokens = await service.login(
            data.email,
            data.password,
            ip_address=request.client.host if request.client else None,
        )
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Issue new access token using a valid refresh token."""
    service = AuthService(db)
    try:
        return await service.refresh_access_token(data.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout current user",
)
async def logout(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Invalidate the current user's refresh token."""
    service = AuthService(db)
    await service.logout(current_user.id)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user profile",
)
async def get_me(current_user: CurrentUser):
    """Return the profile of the currently authenticated user."""
    return current_user
