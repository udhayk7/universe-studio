from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.schemas.job import JobRead
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_service(db: Annotated[Session, Depends(get_db)]) -> JobService:
    return JobService(db)


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: uuid.UUID,
    service: Annotated[JobService, Depends(get_job_service)],
) -> JobRead:
    try:
        return service.get(job_id)
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
