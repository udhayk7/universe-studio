from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.schemas.memory_explorer import (
    MemoryEventRead,
    MemoryLocationRead,
    MemoryObjectRead,
    MemoryRelationshipRead,
    UniverseGraphResponse,
    UniverseMemoryOverview,
)
from app.services.universe_memory_explorer_service import UniverseMemoryExplorerService

router = APIRouter(prefix="/universes/{universe_id}", tags=["memory-explorer"])


def get_memory_explorer_service(
    db: Annotated[Session, Depends(get_db)],
) -> UniverseMemoryExplorerService:
    return UniverseMemoryExplorerService(db)


def not_found_response(error: NotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.get("/memory-overview", response_model=UniverseMemoryOverview)
def get_memory_overview(
    universe_id: uuid.UUID,
    service: Annotated[UniverseMemoryExplorerService, Depends(get_memory_explorer_service)],
) -> UniverseMemoryOverview:
    try:
        return service.overview(universe_id)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/graph", response_model=UniverseGraphResponse)
def get_universe_graph(
    universe_id: uuid.UUID,
    service: Annotated[UniverseMemoryExplorerService, Depends(get_memory_explorer_service)],
) -> UniverseGraphResponse:
    try:
        return service.graph(universe_id)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/events", response_model=list[MemoryEventRead])
def get_universe_events(
    universe_id: uuid.UUID,
    service: Annotated[UniverseMemoryExplorerService, Depends(get_memory_explorer_service)],
) -> list[MemoryEventRead]:
    try:
        return service.events(universe_id)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/relationships", response_model=list[MemoryRelationshipRead])
def get_universe_relationships(
    universe_id: uuid.UUID,
    service: Annotated[UniverseMemoryExplorerService, Depends(get_memory_explorer_service)],
) -> list[MemoryRelationshipRead]:
    try:
        return service.relationships(universe_id)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/locations", response_model=list[MemoryLocationRead])
def get_universe_locations(
    universe_id: uuid.UUID,
    service: Annotated[UniverseMemoryExplorerService, Depends(get_memory_explorer_service)],
) -> list[MemoryLocationRead]:
    try:
        return service.locations(universe_id)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/objects", response_model=list[MemoryObjectRead])
def get_universe_objects(
    universe_id: uuid.UUID,
    service: Annotated[UniverseMemoryExplorerService, Depends(get_memory_explorer_service)],
) -> list[MemoryObjectRead]:
    try:
        return service.objects(universe_id)
    except NotFoundError as error:
        raise not_found_response(error) from error
