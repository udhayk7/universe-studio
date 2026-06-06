from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.universe import Universe
from app.db.session import get_db
from app.schemas.episode_generation import (
    EpisodeGenerateRequest,
    EpisodeRead,
    EpisodeSceneRead,
)
from app.schemas.job import JobRead
from app.services.episode_service import EpisodeService
from app.services.job_service import JobService
from app.workers.episode_worker import run_episode_generation_job

router = APIRouter(tags=["episodes"])


def get_episode_service(db: Annotated[Session, Depends(get_db)]) -> EpisodeService:
    return EpisodeService(db)


@router.post(
    "/universes/{universe_id}/episodes/generate",
    response_model=JobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def generate_episode(
    universe_id: uuid.UUID,
    payload: EpisodeGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
) -> JobRead:
    universe = db.get(Universe, universe_id)
    if universe is None:
        raise _not_found_response(NotFoundError("Universe", universe_id))

    job = JobService(db).create(
        job_type="episode_generation",
        universe_id=universe_id,
        message="Episode generation queued",
    )
    background_tasks.add_task(
        run_episode_generation_job,
        job_id=job.id,
        universe_id=universe_id,
        payload_data=payload.model_dump(mode="json"),
    )
    return job


@router.get("/episodes/{episode_id}", response_model=EpisodeRead)
def get_episode(
    episode_id: uuid.UUID,
    service: Annotated[EpisodeService, Depends(get_episode_service)],
) -> EpisodeRead:
    try:
        return service.get(episode_id)
    except NotFoundError as error:
        raise _not_found_response(error) from error


@router.get("/episodes/{episode_id}/scenes", response_model=list[EpisodeSceneRead])
def get_episode_scenes(
    episode_id: uuid.UUID,
    service: Annotated[EpisodeService, Depends(get_episode_service)],
) -> list[EpisodeSceneRead]:
    try:
        return service.scenes(episode_id)
    except NotFoundError as error:
        raise _not_found_response(error) from error


def _not_found_response(error: NotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
