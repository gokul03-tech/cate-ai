"""
LexOrch-KG — Pydantic Schemas (DTOs)
Request/response schemas for all API endpoints.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# =============================================================================
# Base schemas
# =============================================================================

class BaseResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = True
    message: str = "OK"


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Paginated list response."""
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Auth Schemas
# =============================================================================

class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: str = Field(default="analyst")

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class UserRead(BaseModel):
    """User response schema (no sensitive fields)."""
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """User profile update."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=8)


class AdminUserUpdate(UserUpdate):
    """Admin-only user update."""
    role: Optional[str] = None
    is_active: Optional[bool] = None


# =============================================================================
# Case Schemas
# =============================================================================

class CaseCreate(BaseModel):
    """Case upload request metadata."""
    title: str = Field(min_length=3, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)


class CaseRead(BaseModel):
    """Case response schema."""
    id: UUID
    title: str
    description: Optional[str]
    file_name: str
    file_type: str
    file_size_bytes: int
    status: str
    uploaded_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseDetailRead(CaseRead):
    """Full case detail with related data."""
    metadata_: Optional["CaseMetadataRead"] = None
    agent_executions: list["AgentExecutionRead"] = []
    debate_results: list["DebateResultRead"] = []
    explainability: Optional["ExplainabilityRead"] = None
    reports: list["ReportRead"] = []

    model_config = {"from_attributes": True}


class CaseMetadataRead(BaseModel):
    """Case metadata response."""
    id: UUID
    case_id: UUID
    summary: Optional[str]
    page_count: Optional[int]
    word_count: Optional[int]
    language: Optional[str]
    ocr_applied: bool
    chunks_count: Optional[int]
    case_type: Optional[str]
    jurisdiction: Optional[str]
    filing_date: Optional[str]
    key_facts: Optional[list[str]]
    processing_time_seconds: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Legal Entity Schemas
# =============================================================================

class LegalEntityRead(BaseModel):
    """Legal entity response."""
    id: UUID
    case_id: UUID
    entity_type: str
    entity_value: str
    confidence: Optional[float]
    source_page: Optional[int]
    source_text: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Agent Execution Schemas
# =============================================================================

class AgentExecutionRead(BaseModel):
    """Agent execution step response."""
    id: UUID
    case_id: UUID
    agent_name: str
    agent_step: int
    status: str
    output_data: Optional[dict[str, Any]]
    error_message: Optional[str]
    tokens_used: Optional[int]
    execution_time_seconds: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Debate Schemas
# =============================================================================

class DebateResultRead(BaseModel):
    """Debate result response."""
    id: UUID
    case_id: UUID
    prosecution_argument: Optional[str]
    defense_argument: Optional[str]
    judge_assessment: Optional[str]
    consensus: Optional[str]
    prosecution_confidence: Optional[float]
    defense_confidence: Optional[float]
    final_recommendation: Optional[str]
    recommendation_confidence: Optional[float]
    debate_rounds: int
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Explainability Schemas
# =============================================================================

class ExplainabilityRead(BaseModel):
    """Explainability response."""
    id: UUID
    case_id: UUID
    recommendation: Optional[str] = None
    reasoning_chain: Optional[list[str]] = None
    evidence_used: Optional[list[Any]] = None
    sections_applied: Optional[list[str]]
    precedents_cited: Optional[list[Any]] = None
    confidence_score: Optional[float]
    confidence_breakdown: Optional[dict[str, float]]
    limitations: Optional[list[str]]
    disclaimer: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Human Review Schemas
# =============================================================================

class HumanReviewCreate(BaseModel):
    """Human review submission."""
    decision: str = Field(pattern="^(approved|rejected|needs_revision|pending)$")
    reviewer_notes: Optional[str] = Field(None, max_length=5000)
    override_recommendation: Optional[str] = Field(None, max_length=5000)


class HumanReviewRead(BaseModel):
    """Human review response."""
    id: UUID
    case_id: UUID
    reviewer_id: Optional[UUID]
    decision: str
    reviewer_notes: Optional[str]
    override_recommendation: Optional[str]
    reviewed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Report Schemas
# =============================================================================

class ReportRead(BaseModel):
    """Report metadata response."""
    id: UUID
    case_id: UUID
    format: str
    file_size_bytes: Optional[int]
    download_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Audit Log Schemas
# =============================================================================

class AuditLogRead(BaseModel):
    """Audit log response."""
    id: UUID
    user_id: Optional[UUID]
    case_id: Optional[UUID]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[dict[str, Any]]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Knowledge Graph Schemas
# =============================================================================

class KGNode(BaseModel):
    """Knowledge graph node for React Flow."""
    id: str
    label: str
    data: dict[str, Any]


class KGEdge(BaseModel):
    """Knowledge graph edge for React Flow."""
    source: str
    target: str
    type: str


class KGResponse(BaseModel):
    """Full knowledge graph response."""
    nodes: list[KGNode]
    edges: list[KGEdge]


# =============================================================================
# Agent Trigger Schema
# =============================================================================

class AgentTriggerRequest(BaseModel):
    """Request to trigger agent pipeline for a case."""
    case_id: UUID
    force_rerun: bool = False


class AgentTriggerResponse(BaseModel):
    """Response from triggering agent pipeline."""
    case_id: UUID
    status: str
    message: str
    task_id: Optional[str] = None


# =============================================================================
# Dashboard Stats Schema
# =============================================================================

class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_cases: int
    cases_by_status: dict[str, int]
    total_users: int
    total_reports: int
    recent_cases: list[CaseRead]
    agent_success_rate: float
