"""
LexOrch-KG — All Domain Repositories
Concrete repositories for each ORM model with specialized queries.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.postgres.models import (
    AuditLog,
    Case,
    CaseMetadata,
    LegalEntity,
    RetrievedPrecedent,
    AgentExecution,
    DebateResult,
    Explainability,
    HumanReview,
    Report,
    User,
)
from app.repositories.base import BaseRepository


# =============================================================================
# User Repository
# =============================================================================

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Find user by email (used for login)."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def update_refresh_token(
        self, user_id: UUID, token: Optional[str]
    ) -> None:
        """Store or clear a user's refresh token."""
        await self.db.execute(
            update(User).where(User.id == user_id).values(refresh_token=token)
        )

    async def get_active_users(
        self, offset: int = 0, limit: int = 20
    ) -> list[User]:
        result = await self.db.execute(
            select(User)
            .where(User.is_active == True)
            .offset(offset)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return list(result.scalars().all())


# =============================================================================
# Case Repository
# =============================================================================

class CaseRepository(BaseRepository[Case]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Case, db)

    async def get_with_details(self, case_id: UUID) -> Optional[Case]:
        """Fetch case with all related data eagerly loaded."""
        result = await self.db.execute(
            select(Case)
            .options(
                selectinload(Case.metadata_),
                selectinload(Case.legal_entities),
                selectinload(Case.retrieved_precedents),
                selectinload(Case.agent_executions),
                selectinload(Case.debate_results),
                selectinload(Case.explainability),
                selectinload(Case.human_reviews),
                selectinload(Case.reports),
            )
            .where(Case.id == case_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 20
    ) -> list[Case]:
        result = await self.db.execute(
            select(Case)
            .where(Case.uploaded_by == user_id)
            .offset(offset)
            .limit(limit)
            .order_by(Case.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(self, case_id: UUID, status: str) -> None:
        """Update only the status field (high-frequency operation)."""
        await self.db.execute(
            update(Case).where(Case.id == case_id).values(status=status)
        )


# =============================================================================
# CaseMetadata Repository
# =============================================================================

class CaseMetadataRepository(BaseRepository[CaseMetadata]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(CaseMetadata, db)

    async def get_by_case(self, case_id: UUID) -> Optional[CaseMetadata]:
        result = await self.db.execute(
            select(CaseMetadata).where(CaseMetadata.case_id == case_id)
        )
        return result.scalar_one_or_none()


# =============================================================================
# LegalEntity Repository
# =============================================================================

class LegalEntityRepository(BaseRepository[LegalEntity]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(LegalEntity, db)

    async def get_by_case(self, case_id: UUID) -> list[LegalEntity]:
        result = await self.db.execute(
            select(LegalEntity)
            .where(LegalEntity.case_id == case_id)
            .order_by(LegalEntity.entity_type)
        )
        return list(result.scalars().all())

    async def get_by_type(
        self, case_id: UUID, entity_type: str
    ) -> list[LegalEntity]:
        result = await self.db.execute(
            select(LegalEntity).where(
                LegalEntity.case_id == case_id,
                LegalEntity.entity_type == entity_type,
            )
        )
        return list(result.scalars().all())


# =============================================================================
# RetrievedPrecedent Repository
# =============================================================================

class RetrievedPrecedentRepository(BaseRepository[RetrievedPrecedent]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(RetrievedPrecedent, db)

    async def get_by_case(
        self, case_id: UUID, limit: int = 10
    ) -> list[RetrievedPrecedent]:
        result = await self.db.execute(
            select(RetrievedPrecedent)
            .where(RetrievedPrecedent.case_id == case_id)
            .order_by(RetrievedPrecedent.similarity_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


# =============================================================================
# AgentExecution Repository
# =============================================================================

class AgentExecutionRepository(BaseRepository[AgentExecution]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AgentExecution, db)

    async def get_by_case(self, case_id: UUID) -> list[AgentExecution]:
        result = await self.db.execute(
            select(AgentExecution)
            .where(AgentExecution.case_id == case_id)
            .order_by(AgentExecution.agent_step)
        )
        return list(result.scalars().all())

    async def get_by_case_and_agent(
        self, case_id: UUID, agent_name: str
    ) -> Optional[AgentExecution]:
        result = await self.db.execute(
            select(AgentExecution).where(
                AgentExecution.case_id == case_id,
                AgentExecution.agent_name == agent_name,
            )
        )
        return result.scalar_one_or_none()


# =============================================================================
# DebateResult Repository
# =============================================================================

class DebateResultRepository(BaseRepository[DebateResult]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(DebateResult, db)

    async def get_latest_by_case(
        self, case_id: UUID
    ) -> Optional[DebateResult]:
        result = await self.db.execute(
            select(DebateResult)
            .where(DebateResult.case_id == case_id)
            .order_by(DebateResult.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


# =============================================================================
# Explainability Repository
# =============================================================================

class ExplainabilityRepository(BaseRepository[Explainability]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Explainability, db)

    async def get_by_case(self, case_id: UUID) -> Optional[Explainability]:
        result = await self.db.execute(
            select(Explainability).where(Explainability.case_id == case_id)
        )
        return result.scalar_one_or_none()


# =============================================================================
# HumanReview Repository
# =============================================================================

class HumanReviewRepository(BaseRepository[HumanReview]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(HumanReview, db)

    async def get_by_case(self, case_id: UUID) -> list[HumanReview]:
        result = await self.db.execute(
            select(HumanReview)
            .where(HumanReview.case_id == case_id)
            .order_by(HumanReview.created_at.desc())
        )
        return list(result.scalars().all())


# =============================================================================
# Report Repository
# =============================================================================

class ReportRepository(BaseRepository[Report]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Report, db)

    async def get_by_case(self, case_id: UUID) -> list[Report]:
        result = await self.db.execute(
            select(Report)
            .where(Report.case_id == case_id)
            .order_by(Report.created_at.desc())
        )
        return list(result.scalars().all())

    async def increment_download(self, report_id: UUID) -> None:
        from sqlalchemy import text
        await self.db.execute(
            text("UPDATE reports SET download_count = download_count + 1 WHERE id = :id"),
            {"id": str(report_id)},
        )


# =============================================================================
# AuditLog Repository
# =============================================================================

class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AuditLog, db)

    async def get_recent(
        self, limit: int = 50, user_id: Optional[UUID] = None
    ) -> list[AuditLog]:
        query = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())
