"""
LexOrch-KG — SQLAlchemy ORM Models
All 10 PostgreSQL tables with relationships, indexes, and constraints.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


# =============================================================================
# Enumerations
# =============================================================================

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    JUDGE = "judge"
    LAWYER = "lawyer"
    ANALYST = "analyst"
    VIEWER = "viewer"


class CaseStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    DEBATING = "debating"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ReportFormat(str, enum.Enum):
    PDF = "pdf"
    JSON = "json"
    HTML = "html"


class ReviewDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    PENDING = "pending"


# =============================================================================
# Table 1: Users
# =============================================================================

class User(Base):
    """System users with role-based access control."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.ANALYST)
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    refresh_token = Column(Text, nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    cases = relationship("Case", back_populates="uploaded_by_user", lazy="select")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="select")
    human_reviews = relationship("HumanReview", back_populates="reviewer", lazy="select")

    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"


# =============================================================================
# Table 2: Cases
# =============================================================================

class Case(Base):
    """Legal case document submissions."""

    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt
    file_size_bytes = Column(BigInteger, nullable=False)
    status = Column(Enum(CaseStatus), nullable=False, default=CaseStatus.UPLOADED)
    uploaded_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    uploaded_by_user = relationship("User", back_populates="cases")
    metadata_ = relationship("CaseMetadata", back_populates="case", uselist=False)
    legal_entities = relationship("LegalEntity", back_populates="case")
    retrieved_precedents = relationship("RetrievedPrecedent", back_populates="case")
    agent_executions = relationship("AgentExecution", back_populates="case")
    debate_results = relationship("DebateResult", back_populates="case")
    explainability = relationship("Explainability", back_populates="case", uselist=False)
    human_reviews = relationship("HumanReview", back_populates="case")
    reports = relationship("Report", back_populates="case")
    audit_logs = relationship("AuditLog", back_populates="case")

    __table_args__ = (
        Index("ix_cases_status", "status"),
        Index("ix_cases_uploaded_by", "uploaded_by"),
        Index("ix_cases_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Case {self.title} [{self.status}]>"


# =============================================================================
# Table 3: Case Metadata
# =============================================================================

class CaseMetadata(Base):
    """Extracted metadata from a legal case document."""

    __tablename__ = "case_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    raw_text = Column(Text, nullable=True)           # Full extracted text
    summary = Column(Text, nullable=True)            # LLM-generated summary
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    language = Column(String(10), default="en")
    ocr_applied = Column(Boolean, default=False)
    chunks_count = Column(Integer, nullable=True)
    case_type = Column(String(100), nullable=True)   # Criminal, Civil, etc.
    jurisdiction = Column(String(200), nullable=True)
    filing_date = Column(String(50), nullable=True)
    key_facts = Column(JSON, nullable=True)          # List of key facts
    processing_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    case = relationship("Case", back_populates="metadata_")


# =============================================================================
# Table 4: Legal Entities
# =============================================================================

class LegalEntity(Base):
    """Named entities extracted from case documents."""

    __tablename__ = "legal_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    entity_type = Column(String(100), nullable=False)  # JUDGE, COURT, PERSON, etc.
    entity_value = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)
    source_page = Column(Integer, nullable=True)
    source_text = Column(Text, nullable=True)         # Context snippet
    neo4j_node_id = Column(String(255), nullable=True)  # Neo4j node reference
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    case = relationship("Case", back_populates="legal_entities")

    __table_args__ = (
        Index("ix_legal_entities_case_id", "case_id"),
        Index("ix_legal_entities_entity_type", "entity_type"),
    )


# =============================================================================
# Table 5: Retrieved Precedents
# =============================================================================

class RetrievedPrecedent(Base):
    """Legal precedents retrieved via RAG for a given case."""

    __tablename__ = "retrieved_precedents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    precedent_title = Column(String(500), nullable=False)
    precedent_text = Column(Text, nullable=False)
    similarity_score = Column(Float, nullable=False)
    retrieval_source = Column(String(50), default="chromadb")  # chromadb | neo4j
    chunk_id = Column(String(255), nullable=True)
    page_number = Column(Integer, nullable=True)
    section = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    case = relationship("Case", back_populates="retrieved_precedents")

    __table_args__ = (
        Index("ix_retrieved_precedents_case_id", "case_id"),
        Index("ix_retrieved_precedents_similarity", "similarity_score"),
    )


# =============================================================================
# Table 6: Agent Executions
# =============================================================================

class AgentExecution(Base):
    """Tracks each agent's execution for a case (timeline)."""

    __tablename__ = "agent_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    agent_name = Column(String(100), nullable=False)
    agent_step = Column(Integer, nullable=False)  # Execution order
    status = Column(Enum(AgentStatus), nullable=False, default=AgentStatus.PENDING)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    execution_time_seconds = Column(Float, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    case = relationship("Case", back_populates="agent_executions")

    __table_args__ = (
        Index("ix_agent_executions_case_id", "case_id"),
        Index("ix_agent_executions_agent_name", "agent_name"),
        Index("ix_agent_executions_status", "status"),
    )


# =============================================================================
# Table 7: Debate Results
# =============================================================================

class DebateResult(Base):
    """Multi-agent adversarial debate results per case."""

    __tablename__ = "debate_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    prosecution_argument = Column(Text, nullable=True)
    defense_argument = Column(Text, nullable=True)
    judge_assessment = Column(Text, nullable=True)
    consensus = Column(Text, nullable=True)
    prosecution_confidence = Column(Float, nullable=True)
    defense_confidence = Column(Float, nullable=True)
    final_recommendation = Column(Text, nullable=True)
    recommendation_confidence = Column(Float, nullable=True)
    debate_rounds = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    case = relationship("Case", back_populates="debate_results")

    __table_args__ = (Index("ix_debate_results_case_id", "case_id"),)


# =============================================================================
# Table 8: Explainability
# =============================================================================

class Explainability(Base):
    """XAI outputs — explains why a recommendation was made."""

    __tablename__ = "explainability"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    recommendation = Column(Text, nullable=True)
    reasoning_chain = Column(JSON, nullable=True)   # Step-by-step chain of thought
    evidence_used = Column(JSON, nullable=True)     # List of evidence items
    sections_applied = Column(JSON, nullable=True)  # Legal sections/acts
    precedents_cited = Column(JSON, nullable=True)  # List of cited precedents
    confidence_score = Column(Float, nullable=True)
    confidence_breakdown = Column(JSON, nullable=True)  # Per-factor confidence
    limitations = Column(JSON, nullable=True)           # Known limitations
    disclaimer = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    case = relationship("Case", back_populates="explainability")


# =============================================================================
# Table 9: Human Review
# =============================================================================

class HumanReview(Base):
    """Human expert review and override of AI recommendations."""

    __tablename__ = "human_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision = Column(Enum(ReviewDecision), default=ReviewDecision.PENDING)
    reviewer_notes = Column(Text, nullable=True)
    override_recommendation = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    case = relationship("Case", back_populates="human_reviews")
    reviewer = relationship("User", back_populates="human_reviews")

    __table_args__ = (Index("ix_human_reviews_case_id", "case_id"),)


# =============================================================================
# Table 10: Reports
# =============================================================================

class Report(Base):
    """Generated reports in PDF, JSON, or HTML format."""

    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    format = Column(Enum(ReportFormat), nullable=False)
    file_path = Column(String(1000), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    generated_by_agent = Column(Boolean, default=True)
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    case = relationship("Case", back_populates="reports")

    __table_args__ = (
        Index("ix_reports_case_id", "case_id"),
        Index("ix_reports_format", "format"),
    )


# =============================================================================
# Table 11: Audit Logs
# =============================================================================

class AuditLog(Base):
    """Immutable audit trail for all significant system actions."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="SET NULL"),
        nullable=True,
    )
    action = Column(String(200), nullable=False)       # e.g., "case.upload"
    resource_type = Column(String(100), nullable=True)  # e.g., "Case"
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    case = relationship("Case", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_case_id", "case_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_created_at", "created_at"),
    )
