"""
LexOrch-KG — Reports API Router
Download PDF, JSON, HTML reports.
"""

import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, get_current_user
from app.core.database import get_db
from app.repositories.repositories import ReportRepository
from app.schemas.schemas import ReportRead
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/{case_id}",
    response_model=list[ReportRead],
    summary="List all reports for a case",
)
async def list_reports(
    case_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """List all generated reports for the given case."""
    repo = ReportRepository(db)
    return await repo.get_by_case(case_id)


@router.get(
    "/{report_id}/download",
    summary="Download a report file",
)
async def download_report(
    report_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Download a report in its original format (PDF / JSON / HTML).
    Increments the download counter.
    """
    repo = ReportRepository(db)
    report = await repo.get_by_id(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    file_path = report.file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found on disk",
        )

    # Increment download count
    await repo.increment_download(report_id)

    # Map format to MIME type
    mime_types = {
        "pdf": "application/pdf",
        "json": "application/json",
        "html": "text/html",
    }
    media_type = mime_types.get(report.format.value, "application/octet-stream")
    filename = os.path.basename(file_path)

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
