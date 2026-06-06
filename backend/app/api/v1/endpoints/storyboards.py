from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.schemas.storyboard import EpisodeStoryboardRead, ShotRead, StoryboardRenderRequest
from app.services.storyboard_service import StoryboardService

router = APIRouter(tags=["storyboards"])


def get_storyboard_service(db: Annotated[Session, Depends(get_db)]) -> StoryboardService:
    return StoryboardService(db)


@router.get("/shots/{shot_id}", response_model=ShotRead)
def get_shot(
    shot_id: uuid.UUID,
    service: Annotated[StoryboardService, Depends(get_storyboard_service)],
) -> ShotRead:
    try:
        return service.get_shot(shot_id)
    except NotFoundError as error:
        raise _not_found_response(error) from error


@router.get("/storyboards/{episode_id}", response_model=EpisodeStoryboardRead)
def get_storyboard(
    episode_id: uuid.UUID,
    service: Annotated[StoryboardService, Depends(get_storyboard_service)],
) -> EpisodeStoryboardRead:
    try:
        return service.get_storyboard(episode_id)
    except NotFoundError as error:
        raise _not_found_response(error) from error


@router.post("/episodes/{episode_id}/storyboard/render", response_model=EpisodeStoryboardRead)
def render_storyboard(
    episode_id: uuid.UUID,
    payload: StoryboardRenderRequest,
    service: Annotated[StoryboardService, Depends(get_storyboard_service)],
) -> EpisodeStoryboardRead:
    try:
        return service.render_episode(
            episode_id,
            regenerate_images=payload.regenerate_images,
        )
    except NotFoundError as error:
        raise _not_found_response(error) from error


def _not_found_response(error: NotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
