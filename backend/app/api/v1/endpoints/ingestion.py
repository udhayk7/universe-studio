from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.universe import Universe
from app.db.session import get_db
from app.schemas.job import JobRead
from app.schemas.source import SourcePayload, SourceType
from app.services.job_service import JobService
from app.services.source_ingestion_service import SourceIngestionService
from app.workers.extraction_worker import run_extraction_job

router = APIRouter(tags=["ingestion"])


@router.post(
    "/universes/create-from-input",
    response_model=JobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_universe_from_input(
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    source_type: Annotated[SourceType, Form()],
    content: Annotated[str | None, Form()] = None,
    title_hint: Annotated[str | None, Form()] = None,
    genre_hint: Annotated[str | None, Form()] = None,
    tone_hint: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
) -> JobRead:
    payload = await _build_source_payload(
        source_type=source_type,
        content=content,
        title_hint=title_hint,
        genre_hint=genre_hint,
        tone_hint=tone_hint,
        file=file,
    )
    job = JobService(db).create(
        job_type="universe_extraction",
        message="Universe extraction queued",
    )
    background_tasks.add_task(
        run_extraction_job,
        job_id=job.id,
        payload_data=payload.model_dump(mode="json"),
        universe_id=None,
    )
    return job


@router.post(
    "/universes/{universe_id}/ingest",
    response_model=JobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_universe_source(
    universe_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    source_type: Annotated[SourceType, Form()],
    content: Annotated[str | None, Form()] = None,
    title_hint: Annotated[str | None, Form()] = None,
    genre_hint: Annotated[str | None, Form()] = None,
    tone_hint: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
) -> JobRead:
    universe = db.get(Universe, universe_id)
    if universe is None:
        raise _not_found_response(NotFoundError("Universe", universe_id))

    payload = await _build_source_payload(
        source_type=source_type,
        content=content,
        title_hint=title_hint,
        genre_hint=genre_hint,
        tone_hint=tone_hint,
        file=file,
    )
    job = JobService(db).create(
        job_type="universe_ingestion",
        universe_id=universe_id,
        message="Universe ingestion queued",
    )
    background_tasks.add_task(
        run_extraction_job,
        job_id=job.id,
        payload_data=payload.model_dump(mode="json"),
        universe_id=universe_id,
    )
    return job


async def _build_source_payload(
    *,
    source_type: SourceType,
    content: str | None,
    title_hint: str | None,
    genre_hint: str | None,
    tone_hint: str | None,
    file: UploadFile | None,
) -> SourcePayload:
    file_bytes = await file.read() if file else None
    try:
        return SourceIngestionService().build_payload(
            source_type=source_type,
            content=content,
            file_bytes=file_bytes,
            filename=file.filename if file else None,
            mime_type=file.content_type if file else None,
            title_hint=title_hint,
            genre_hint=genre_hint,
            tone_hint=tone_hint,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


def _not_found_response(error: NotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
