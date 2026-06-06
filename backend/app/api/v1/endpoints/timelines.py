from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.schemas.job import JobRead
from app.schemas.timeline import TimelineCreate, TimelineRead, TimelineUpdate
from app.schemas.timeline_branching import (
    FutureGenerateRequest,
    TimelineBranchCreate,
    TimelineBranchRead,
    TimelineCommitRead,
    TimelineDiffResponse,
    TimelineEventRead,
)
from app.services.branch_service import BranchService
from app.services.future_regeneration_service import FutureRegenerationService
from app.services.timeline_diff_service import TimelineDiffService
from app.services.timeline_history_service import TimelineHistoryService
from app.services.timeline_service import TimelineService
from app.workers.episode_worker import run_episode_generation_job

router = APIRouter(tags=["timelines"])


def get_timeline_service(db: Annotated[Session, Depends(get_db)]) -> TimelineService:
    return TimelineService(db)


def not_found_response(error: NotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


def bad_request_response(error: ValueError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post(
    "/universes/{universe_id}/timelines",
    response_model=TimelineRead,
    status_code=status.HTTP_201_CREATED,
)
def create_timeline(
    universe_id: uuid.UUID,
    payload: TimelineCreate,
    service: Annotated[TimelineService, Depends(get_timeline_service)],
) -> TimelineRead:
    try:
        return service.create(universe_id, payload)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/universes/{universe_id}/timelines", response_model=list[TimelineRead])
def list_timelines(
    universe_id: uuid.UUID,
    service: Annotated[TimelineService, Depends(get_timeline_service)],
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[TimelineRead]:
    try:
        return service.list_by_universe(universe_id, limit=limit, offset=offset)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/timelines/diff", response_model=TimelineDiffResponse)
def diff_timelines(
    base_timeline_id: uuid.UUID,
    compare_timeline_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> TimelineDiffResponse:
    try:
        return TimelineDiffService(db).diff(
            base_timeline_id=base_timeline_id,
            compare_timeline_id=compare_timeline_id,
        )
    except NotFoundError as error:
        raise not_found_response(error) from error
    except ValueError as error:
        raise bad_request_response(error) from error


@router.get("/timelines/{timeline_id}", response_model=TimelineRead)
def get_timeline(
    timeline_id: uuid.UUID,
    service: Annotated[TimelineService, Depends(get_timeline_service)],
) -> TimelineRead:
    try:
        return service.get(timeline_id)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/timelines/{timeline_id}/commits", response_model=list[TimelineCommitRead])
def get_timeline_commits(
    timeline_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[TimelineCommitRead]:
    try:
        return TimelineHistoryService(db).commits(timeline_id)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/timelines/{timeline_id}/events", response_model=list[TimelineEventRead])
def get_timeline_events(
    timeline_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[TimelineEventRead]:
    try:
        return TimelineHistoryService(db).events(timeline_id)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.post(
    "/timelines/{timeline_id}/branch",
    response_model=TimelineBranchRead,
    status_code=status.HTTP_201_CREATED,
)
def create_timeline_branch(
    timeline_id: uuid.UUID,
    payload: TimelineBranchCreate,
    db: Annotated[Session, Depends(get_db)],
) -> TimelineBranchRead:
    try:
        return BranchService(db).create_branch(
            source_timeline_id=timeline_id,
            payload=payload,
        )
    except NotFoundError as error:
        raise not_found_response(error) from error
    except ValueError as error:
        raise bad_request_response(error) from error


@router.post(
    "/timelines/{timeline_id}/generate-future",
    response_model=JobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def generate_timeline_future(
    timeline_id: uuid.UUID,
    payload: FutureGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
) -> JobRead:
    try:
        timeline = TimelineHistoryService(db).get_timeline(timeline_id)
        job = FutureRegenerationService(db).create_generation_job(timeline_id)
    except NotFoundError as error:
        raise not_found_response(error) from error

    background_tasks.add_task(
        run_episode_generation_job,
        job_id=job.id,
        universe_id=timeline.universe_id,
        timeline_id=timeline.id,
        payload_data=payload.model_dump(mode="json"),
    )
    return job


@router.patch("/timelines/{timeline_id}", response_model=TimelineRead)
def update_timeline(
    timeline_id: uuid.UUID,
    payload: TimelineUpdate,
    service: Annotated[TimelineService, Depends(get_timeline_service)],
) -> TimelineRead:
    try:
        return service.update(timeline_id, payload)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.delete("/timelines/{timeline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timeline(
    timeline_id: uuid.UUID,
    service: Annotated[TimelineService, Depends(get_timeline_service)],
) -> None:
    try:
        service.delete(timeline_id)
    except NotFoundError as error:
        raise not_found_response(error) from error
