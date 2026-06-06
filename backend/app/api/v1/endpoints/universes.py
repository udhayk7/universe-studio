from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.schemas.universe import UniverseCreate, UniverseRead, UniverseUpdate
from app.services.universe_service import UniverseService

router = APIRouter(prefix="/universes", tags=["universes"])


def get_universe_service(db: Annotated[Session, Depends(get_db)]) -> UniverseService:
    return UniverseService(db)


def not_found_response(error: NotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.post("", response_model=UniverseRead, status_code=status.HTTP_201_CREATED)
def create_universe(
    payload: UniverseCreate,
    service: Annotated[UniverseService, Depends(get_universe_service)],
) -> UniverseRead:
    return service.create(payload)


@router.get("", response_model=list[UniverseRead])
def list_universes(
    service: Annotated[UniverseService, Depends(get_universe_service)],
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[UniverseRead]:
    return service.list(limit=limit, offset=offset)


@router.get("/{universe_id}", response_model=UniverseRead)
def get_universe(
    universe_id: uuid.UUID,
    service: Annotated[UniverseService, Depends(get_universe_service)],
) -> UniverseRead:
    try:
        return service.get(universe_id)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.patch("/{universe_id}", response_model=UniverseRead)
def update_universe(
    universe_id: uuid.UUID,
    payload: UniverseUpdate,
    service: Annotated[UniverseService, Depends(get_universe_service)],
) -> UniverseRead:
    try:
        return service.update(universe_id, payload)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.delete("/{universe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_universe(
    universe_id: uuid.UUID,
    service: Annotated[UniverseService, Depends(get_universe_service)],
) -> None:
    try:
        service.delete(universe_id)
    except NotFoundError as error:
        raise not_found_response(error) from error
