"""
LexOrch-KG — Async Database Engine & Session Factory
SQLAlchemy 2.0 async setup with connection pooling.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ---------------------------------------------------------------------------
engine_kwargs = {
    "echo": settings.debug,
}

# Apply connection pooling only for PostgreSQL/MySQL
if not settings.database_url.startswith("sqlite"):
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
    })

engine = create_async_engine(
    settings.database_url,
    **engine_kwargs,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,   # Objects remain usable after commit
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Declarative Base for all ORM models
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ---------------------------------------------------------------------------
# Dependency injection — FastAPI dependency
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.
    Session is automatically closed after request completes.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager version for use outside FastAPI request scope."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
