"""
LexOrch-KG — Admin API Router
User management, audit logs, and system statistics.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import CurrentUser, require_roles
from app.core.database import get_db
from app.infrastructure.postgres.models import Case, User
from app.repositories.repositories import AuditLogRepository, UserRepository
from app.schemas.schemas import AdminUserUpdate, AuditLogRead, DashboardStats, UserRead

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/users",
    response_model=list[UserRead],
    dependencies=[Depends(require_roles("admin"))],
    summary="List all users",
)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all registered users. Admin only."""
    repo = UserRepository(db)
    offset = (page - 1) * page_size
    return await repo.get_active_users(offset=offset, limit=page_size)


@router.patch(
    "/users/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_roles("admin"))],
    summary="Update a user (admin)",
)
async def update_user(
    user_id: UUID,
    update: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update user role, status, or profile. Admin only."""
    from app.core.security import get_password_hash

    repo = UserRepository(db)
    kwargs = update.model_dump(exclude_none=True)

    if "password" in kwargs:
        kwargs["hashed_password"] = get_password_hash(kwargs.pop("password"))

    if "role" in kwargs:
        from app.infrastructure.postgres.models import UserRole
        try:
            kwargs["role"] = UserRole(kwargs["role"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {kwargs['role']}",
            )

    user = await repo.update(user_id, **kwargs)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
    summary="Deactivate a user",
)
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user account (soft disable). Admin only."""
    repo = UserRepository(db)
    user = await repo.update(user_id, is_active=False)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get(
    "/audit-logs",
    response_model=list[AuditLogRead],
    dependencies=[Depends(require_roles("admin"))],
    summary="View audit logs",
)
async def get_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    user_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """View system audit logs. Admin only."""
    repo = AuditLogRepository(db)
    return await repo.get_recent(limit=limit, user_id=user_id)


@router.get(
    "/stats",
    response_model=DashboardStats,
    dependencies=[Depends(require_roles("admin", "judge", "analyst"))],
    summary="Get dashboard statistics",
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """Return aggregate statistics for the admin dashboard."""
    # Total cases
    total_cases_result = await db.execute(select(func.count(Case.id)))
    total_cases = total_cases_result.scalar_one()

    # Cases by status
    status_result = await db.execute(
        select(Case.status, func.count(Case.id)).group_by(Case.status)
    )
    cases_by_status = {str(row[0].value): row[1] for row in status_result.all()}

    # Total users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar_one()

    # Total reports
    from app.infrastructure.postgres.models import Report
    total_reports_result = await db.execute(select(func.count(Report.id)))
    total_reports = total_reports_result.scalar_one()

    # Recent cases
    from app.repositories.repositories import CaseRepository
    case_repo = CaseRepository(db)
    recent_cases = await case_repo.get_all(offset=0, limit=5)

    # Agent success rate (completed / total)
    from app.infrastructure.postgres.models import AgentExecution
    total_exec = await db.execute(select(func.count(AgentExecution.id)))
    completed_exec = await db.execute(
        select(func.count(AgentExecution.id)).where(
            AgentExecution.status == "completed"
        )
    )
    total_e = total_exec.scalar_one() or 1
    completed_e = completed_exec.scalar_one()
    success_rate = completed_e / total_e

    return DashboardStats(
        total_cases=total_cases,
        cases_by_status=cases_by_status,
        total_users=total_users,
        total_reports=total_reports,
        recent_cases=recent_cases,
        agent_success_rate=round(success_rate, 3),
    )
