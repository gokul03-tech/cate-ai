"""
LexOrch-KG — Authentication Service
Handles user registration, login, token refresh, and admin bootstrap.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_refresh_token,
)
from app.infrastructure.postgres.models import User, UserRole
from app.repositories.repositories import UserRepository, AuditLogRepository
from app.schemas.schemas import UserRegister, TokenResponse


class AuthService:
    """Authentication and session management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditLogRepository(db)

    async def register(
        self,
        data: UserRegister,
        ip_address: Optional[str] = None,
    ) -> User:
        """
        Register a new user.
        
        Raises:
            ValueError: If email already registered or role invalid
        """
        # Check for duplicate email
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ValueError(f"Email {data.email} is already registered")

        # Validate role
        try:
            role = UserRole(data.role.lower())
        except ValueError:
            role = UserRole.ANALYST  # Default role

        user = await self.user_repo.create(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            role=role,
            is_active=True,
            is_verified=False,
        )

        # Audit log
        await self.audit_repo.create(
            user_id=user.id,
            action="auth.register",
            resource_type="User",
            resource_id=str(user.id),
            details={"email": data.email, "role": role.value},
            ip_address=ip_address,
        )

        logger.info(f"New user registered: {user.email} [{user.role}]")
        return user

    async def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
    ) -> TokenResponse:
        """
        Authenticate user and return JWT token pair.
        
        Raises:
            ValueError: If credentials invalid or account inactive
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is disabled. Please contact support.")

        # Generate token pair
        access_token = create_access_token(
            subject=user.id,
            role=user.role.value,
        )
        refresh_token = create_refresh_token(subject=user.id)

        # Store refresh token hash
        await self.user_repo.update_refresh_token(user.id, refresh_token)

        # Update last login
        await self.user_repo.update(
            user.id, last_login=datetime.now(timezone.utc)
        )

        # Audit log
        await self.audit_repo.create(
            user_id=user.id,
            action="auth.login",
            resource_type="User",
            resource_id=str(user.id),
            ip_address=ip_address,
        )

        from app.core.config import settings
        logger.info(f"User logged in: {user.email}")
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Issue new access token using a valid refresh token."""
        try:
            payload = verify_refresh_token(refresh_token)
            user_id = UUID(payload["sub"])
        except Exception as e:
            raise ValueError(f"Invalid refresh token: {e}")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        if user.refresh_token != refresh_token:
            raise ValueError("Refresh token mismatch — possible token reuse")

        # Issue new tokens (token rotation)
        new_access = create_access_token(subject=user.id, role=user.role.value)
        new_refresh = create_refresh_token(subject=user.id)
        await self.user_repo.update_refresh_token(user.id, new_refresh)

        from app.core.config import settings
        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def logout(self, user_id: UUID) -> None:
        """Invalidate refresh token on logout."""
        await self.user_repo.update_refresh_token(user_id, None)
        logger.info(f"User {user_id} logged out")
