"""
LexOrch-KG — Case Service
Handles case uploads, file processing, status tracking, and pipeline invocation.
"""

import os
import shutil
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import aiofiles
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.postgres.models import CaseStatus
from app.repositories.repositories import (
    AgentExecutionRepository,
    AuditLogRepository,
    CaseMetadataRepository,
    CaseRepository,
    DebateResultRepository,
    ExplainabilityRepository,
    LegalEntityRepository,
    ReportRepository,
    RetrievedPrecedentRepository,
)
from app.schemas.schemas import CaseCreate


class CaseService:
    """
    Manages the full case lifecycle:
    upload → store → trigger pipeline → persist results
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.case_repo = CaseRepository(db)
        self.metadata_repo = CaseMetadataRepository(db)
        self.entity_repo = LegalEntityRepository(db)
        self.precedent_repo = RetrievedPrecedentRepository(db)
        self.agent_repo = AgentExecutionRepository(db)
        self.debate_repo = DebateResultRepository(db)
        self.explain_repo = ExplainabilityRepository(db)
        self.report_repo = ReportRepository(db)
        self.audit_repo = AuditLogRepository(db)

    async def create_case(
        self,
        metadata: CaseCreate,
        file_content: bytes,
        file_name: str,
        user_id: UUID,
    ) -> "Case":
        """
        Save uploaded file and create case record.
        
        Returns the created Case ORM object.
        """
        # Validate file type
        extension = file_name.rsplit(".", 1)[-1].lower()
        if extension not in settings.allowed_extensions_list:
            raise ValueError(
                f"File type '{extension}' not allowed. "
                f"Allowed: {settings.allowed_extensions_list}"
            )

        # Validate file size
        if len(file_content) > settings.max_file_size_bytes:
            raise ValueError(
                f"File size {len(file_content) / 1024 / 1024:.1f}MB "
                f"exceeds limit of {settings.max_file_size_mb}MB"
            )

        # Persist file to uploads directory
        os.makedirs(settings.upload_dir, exist_ok=True)
        import uuid
        stored_name = f"{uuid.uuid4()}.{extension}"
        file_path = os.path.join(settings.upload_dir, stored_name)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)

        logger.info(f"File saved: {file_path} ({len(file_content)} bytes)")

        # Create case record in DB
        case = await self.case_repo.create(
            title=metadata.title,
            description=metadata.description,
            file_name=file_name,
            file_path=file_path,
            file_type=extension,
            file_size_bytes=len(file_content),
            status=CaseStatus.UPLOADED,
            uploaded_by=user_id,
        )

        # Audit log
        await self.audit_repo.create(
            user_id=user_id,
            case_id=case.id,
            action="case.upload",
            resource_type="Case",
            resource_id=str(case.id),
            details={"file_name": file_name, "size_bytes": len(file_content)},
        )

        return case

    async def trigger_pipeline(
        self, case_id: UUID, user_id: UUID
    ) -> None:
        """
        Trigger the 8-agent AI pipeline for a case.
        Runs asynchronously — updates case status and persists results.
        """
        case = await self.case_repo.get_by_id(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        # Update status to processing
        await self.case_repo.update_status(case_id, CaseStatus.PROCESSING)

        # Audit
        await self.audit_repo.create(
            user_id=user_id,
            case_id=case_id,
            action="case.pipeline_triggered",
            resource_type="Case",
            resource_id=str(case_id),
        )

        # Run pipeline asynchronously (fire-and-forget with DB persistence)
        import asyncio
        asyncio.create_task(
            self._run_pipeline_and_persist(case_id, case)
        )

    async def _run_pipeline_and_persist(self, case_id: UUID, case) -> None:
        """
        Internal: Run the AI pipeline and persist all results to PostgreSQL.
        """
        from app.agents.orchestrator import get_pipeline
        from app.core.database import get_db_context

        try:
            pipeline = get_pipeline()

            logger.info(f"Running pipeline for case {case_id}")

            final_state = await pipeline.run(
                case_id=str(case_id),
                case_title=case.title,
                file_path=case.file_path,
                file_type=case.file_type,
            )

            # Persist results in a new DB session (pipeline runs outside request scope)
            async with get_db_context() as db:
                await self._persist_pipeline_results(db, case_id, final_state)

        except Exception as e:
            logger.error(f"Pipeline failed for case {case_id}: {e}")
            # Update case status to failed
            from app.core.database import get_db_context
            async with get_db_context() as db:
                repo = CaseRepository(db)
                await repo.update_status(case_id, CaseStatus.FAILED)

    async def _persist_pipeline_results(
        self,
        db: AsyncSession,
        case_id: UUID,
        state: dict,
    ) -> None:
        """Persist all agent outputs to their respective PostgreSQL tables."""
        from datetime import datetime, timezone

        # ── Case Metadata ─────────────────────────────────────────────────────
        meta_repo = CaseMetadataRepository(db)
        await meta_repo.create(
            case_id=case_id,
            raw_text=state.get("raw_text", "")[:100000],  # Limit storage
            summary=state.get("summary"),
            page_count=state.get("page_count"),
            word_count=state.get("word_count"),
            ocr_applied=state.get("ocr_applied", False),
            chunks_count=len(state.get("chunks", [])),
            key_facts=state.get("key_facts", []),
        )

        # ── Legal Entities ────────────────────────────────────────────────────
        entity_repo = LegalEntityRepository(db)
        for entity in state.get("entities", [])[:200]:  # Limit to 200
            await entity_repo.create(
                case_id=case_id,
                entity_type=entity.get("type", "UNKNOWN"),
                entity_value=entity.get("value", ""),
                confidence=entity.get("confidence"),
                source_text=entity.get("context", "")[:500],
            )

        # ── Retrieved Precedents ──────────────────────────────────────────────
        prec_repo = RetrievedPrecedentRepository(db)
        for prec in state.get("retrieved_precedents", [])[:20]:
            await prec_repo.create(
                case_id=case_id,
                precedent_title=prec.get("title", "Unknown"),
                precedent_text=prec.get("text", "")[:2000],
                similarity_score=prec.get("similarity_score", 0),
                retrieval_source=prec.get("source", "chromadb"),
                chunk_id=prec.get("metadata", {}).get("chunk_id"),
                page_number=prec.get("metadata", {}).get("page_number"),
                section=prec.get("metadata", {}).get("section"),
            )

        # ── Agent Executions ──────────────────────────────────────────────────
        agent_names = [
            "CaseUnderstandingAgent", "EntityExtractionAgent",
            "KnowledgeGraphAgent", "RetrievalAgent", "ReasoningAgent",
            "DebateAgent", "ExplainabilityAgent", "ReportAgent",
        ]
        agent_repo = AgentExecutionRepository(db)
        completed = state.get("completed_agents", [])
        for step, name in enumerate(agent_names, 1):
            status = "completed" if name in completed else "failed"
            await agent_repo.create(
                case_id=case_id,
                agent_name=name,
                agent_step=step,
                status=status,
                completed_at=datetime.now(timezone.utc) if status == "completed" else None,
            )

        # ── Debate Result ─────────────────────────────────────────────────────
        debate = state.get("debate_result", {})
        if debate:
            debate_repo = DebateResultRepository(db)
            await debate_repo.create(
                case_id=case_id,
                prosecution_argument=debate.get("prosecution_argument"),
                defense_argument=debate.get("defense_argument"),
                judge_assessment=debate.get("judge_assessment"),
                consensus=debate.get("consensus"),
                prosecution_confidence=debate.get("prosecution_confidence"),
                defense_confidence=debate.get("defense_confidence"),
                final_recommendation=debate.get("final_recommendation"),
                recommendation_confidence=debate.get("recommendation_confidence"),
                debate_rounds=debate.get("debate_rounds", 1),
            )

        # ── Explainability ────────────────────────────────────────────────────
        explain = state.get("explainability", {})
        if explain:
            explain_repo = ExplainabilityRepository(db)
            await explain_repo.create(
                case_id=case_id,
                recommendation=explain.get("recommendation"),
                reasoning_chain=explain.get("reasoning_chain"),
                evidence_used=explain.get("evidence_used"),
                sections_applied=explain.get("sections_applied"),
                precedents_cited=explain.get("precedents_cited"),
                confidence_score=explain.get("confidence_score"),
                confidence_breakdown=explain.get("confidence_breakdown"),
                limitations=explain.get("limitations"),
                disclaimer=explain.get("disclaimer"),
            )

        # ── Reports ───────────────────────────────────────────────────────────
        generated = state.get("generated_reports", {})
        report_repo = ReportRepository(db)
        from app.infrastructure.postgres.models import ReportFormat
        for fmt_str, report_data in generated.items():
            try:
                fmt = ReportFormat(fmt_str)
                await report_repo.create(
                    case_id=case_id,
                    format=fmt,
                    file_path=report_data.get("path"),
                    file_size_bytes=report_data.get("size"),
                    generated_by_agent=True,
                )
            except Exception as e:
                logger.error(f"Failed to save report record: {e}")

        # ── Update case status to COMPLETED ───────────────────────────────────
        case_repo = CaseRepository(db)
        await case_repo.update_status(case_id, CaseStatus.COMPLETED)
        logger.success(f"Pipeline results persisted for case {case_id}")

    async def get_case(self, case_id: UUID) -> Optional[object]:
        """Get case with all related data."""
        return await self.case_repo.get_with_details(case_id)

    async def list_cases(
        self,
        user_id: Optional[UUID],
        role: str,
        offset: int = 0,
        limit: int = 20,
    ) -> list:
        """List cases — admins see all, others see only their own."""
        if role == "admin":
            return await self.case_repo.get_all(offset=offset, limit=limit)
        else:
            return await self.case_repo.get_by_user(user_id, offset, limit)
