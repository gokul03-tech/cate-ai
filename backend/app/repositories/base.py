"""
LexOrch-KG — Repository Pattern Base Class
Generic async CRUD operations for all ORM models.
"""

from typing import Any, Generic, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic async repository providing CRUD operations.
    
    All repositories inherit from this class and get:
    - create, get_by_id, get_all, update, delete
    - count, exists
    - Pagination support
    """

    def __init__(self, model: Type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def create(self, **kwargs: Any) -> ModelType:
        """Create and persist a new model instance."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def get_by_id(self, id: UUID | str) -> Optional[ModelType]:
        """Fetch a record by primary key (UUID)."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
        **filters: Any,
    ) -> list[ModelType]:
        """Fetch paginated list with optional equality filters."""
        query = select(self.model)
        for field, value in filters.items():
            if value is not None and hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        query = query.offset(offset).limit(limit).order_by(self.model.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, id: UUID | str, **kwargs: Any) -> Optional[ModelType]:
        """Update fields of an existing record."""
        instance = await self.get_by_id(id)
        if not instance:
            return None
        for field, value in kwargs.items():
            if value is not None and hasattr(instance, field):
                setattr(instance, field, value)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: UUID | str) -> bool:
        """Soft-delete (if applicable) or hard-delete a record."""
        instance = await self.get_by_id(id)
        if not instance:
            return False
        await self.db.delete(instance)
        await self.db.flush()
        return True

    async def count(self, **filters: Any) -> int:
        """Count records matching optional filters."""
        query = select(func.count()).select_from(self.model)
        for field, value in filters.items():
            if value is not None and hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def exists(self, **filters: Any) -> bool:
        """Check if a record matching filters exists."""
        count = await self.count(**filters)
        return count > 0
