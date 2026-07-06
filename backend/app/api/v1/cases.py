"""
LexOrch-KG — Cases API Router
Upload, list, detail, pipeline trigger, knowledge graph, entities, debate, explainability.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, require_roles
from app.core.database import get_db
from app.infrastructure.neo4j.client import neo4j_client
from app.repositories.repositories import (
    AuditLogRepository,
    CaseRepository,
    DebateResultRepository,
    ExplainabilityRepository,
    HumanReviewRepository,
    LegalEntityRepository,
    RetrievedPrecedentRepository,
)
from app.schemas.schemas import (
    AgentTriggerRequest,
    AgentTriggerResponse,
    CaseDetailRead,
    CaseRead,
    DebateResultRead,
    ExplainabilityRead,
    HumanReviewCreate,
    HumanReviewRead,
    KGResponse,
    LegalEntityRead,
    PaginatedResponse,
)
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.post(
    "/upload",
    response_model=CaseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a legal case document",
)
async def upload_case(
    title: str = Form(..., description="Case title"),
    description: Optional[str] = Form(None),
    file: UploadFile = File(..., description="PDF, DOCX, or TXT file"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a legal document (PDF/DOCX/TXT).
    
    The file is stored securely and a case record is created.
    Use POST /cases/{id}/analyze to trigger the AI pipeline.
    """
    from app.schemas.schemas import CaseCreate

    service = CaseService(db)
    file_content = await file.read()

    try:
        case = await service.create_case(
            metadata=CaseCreate(title=title, description=description),
            file_content=file_content,
            file_name=file.filename or "document",
            user_id=current_user.id,
        )
        return case
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{case_id}/analyze",
    response_model=AgentTriggerResponse,
    summary="Trigger AI analysis pipeline",
)
async def analyze_case(
    case_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger the 8-agent AI pipeline for a case.
    
    Pipeline runs asynchronously. Poll GET /cases/{id} for status updates.
    """
    service = CaseService(db)
    try:
        await service.trigger_pipeline(case_id, current_user.id)
        return AgentTriggerResponse(
            case_id=case_id,
            status="processing",
            message="AI pipeline triggered successfully. Analysis is running in the background.",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/",
    response_model=list[CaseRead],
    summary="List all cases",
)
async def list_cases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List cases. Admins see all cases; others see only their own."""
    service = CaseService(db)
    offset = (page - 1) * page_size
    cases = await service.list_cases(
        user_id=current_user.id,
        role=current_user.role.value,
        offset=offset,
        limit=page_size,
    )
    return cases


@router.get(
    "/{case_id}",
    response_model=CaseDetailRead,
    summary="Get case details with all agent outputs",
)
async def get_case(
    case_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full case detail including all agent execution results."""
    service = CaseService(db)
    case = await service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


@router.get(
    "/{case_id}/entities",
    response_model=list[LegalEntityRead],
    summary="Get extracted legal entities",
)
async def get_entities(
    case_id: UUID,
    entity_type: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all legal entities extracted from the case document."""
    repo = LegalEntityRepository(db)
    if entity_type:
        entities = await repo.get_by_type(case_id, entity_type.upper())
    else:
        entities = await repo.get_by_case(case_id)
    return entities


@router.get(
    "/{case_id}/knowledge-graph",
    response_model=KGResponse,
    summary="Get knowledge graph visualization data",
)
async def get_knowledge_graph(
    case_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Retrieve nodes and edges for the case knowledge graph.
    Response is formatted for React Flow visualization.
    """
    try:
        graph_data = await neo4j_client.get_case_graph(str(case_id))
        return KGResponse(
            nodes=[{"id": n["id"], "label": n["label"], "data": n["data"]} for n in graph_data.get("nodes", [])],
            edges=[{"source": e["source"], "target": e["target"], "type": e["type"]} for e in graph_data.get("edges", [])],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Knowledge graph unavailable: {e}",
        )


@router.get(
    "/{case_id}/debate",
    response_model=DebateResultRead,
    summary="Get multi-agent debate results",
)
async def get_debate(
    case_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the adversarial debate transcript for this case."""
    repo = DebateResultRepository(db)
    debate = await repo.get_latest_by_case(case_id)
    if not debate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debate not yet generated for this case",
        )
    return debate


@router.get(
    "/{case_id}/explainability",
    response_model=ExplainabilityRead,
    summary="Get AI explainability report",
)
async def get_explainability(
    case_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the XAI explanation for this case.
    
    Includes reasoning chain, evidence, confidence breakdown, and disclaimer.
    """
    repo = ExplainabilityRepository(db)
    explain = await repo.get_by_case(case_id)
    if not explain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Explainability report not yet generated",
        )
    return explain


@router.post(
    "/{case_id}/review",
    response_model=HumanReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit human review for a case",
)
async def submit_review(
    case_id: UUID,
    review: HumanReviewCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "judge", "lawyer")),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a human legal expert's review of the AI recommendation.
    
    Required role: judge, lawyer, or admin.
    """
    from datetime import datetime, timezone
    repo = HumanReviewRepository(db)
    record = await repo.create(
        case_id=case_id,
        reviewer_id=current_user.id,
        decision=review.decision,
        reviewer_notes=review.reviewer_notes,
        override_recommendation=review.override_recommendation,
        reviewed_at=datetime.now(timezone.utc),
    )
    return record


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
    summary="Delete a case (admin only)",
)
async def delete_case(
    case_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a case and all associated data. Admin only."""
    repo = CaseRepository(db)
    deleted = await repo.delete(case_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
