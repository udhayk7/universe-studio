from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.schemas.character import CharacterCreate, CharacterRead, CharacterUpdate
from app.schemas.character_memory import (
    CharacterArcResponse,
    CharacterContextPack,
    CharacterKnowledgeResponse,
    CharacterMemoryResponse,
    CharacterRelationshipResponse,
    CharacterStateResponse,
)
from app.services.character_arc_service import CharacterArcService
from app.services.character_knowledge_service import CharacterKnowledgeService
from app.services.character_memory_service import CharacterMemoryService
from app.services.character_service import CharacterService

router = APIRouter(tags=["characters"])


def get_character_service(db: Annotated[Session, Depends(get_db)]) -> CharacterService:
    return CharacterService(db)


def get_character_memory_service(
    db: Annotated[Session, Depends(get_db)],
) -> CharacterMemoryService:
    return CharacterMemoryService(db)


def get_character_knowledge_service(
    db: Annotated[Session, Depends(get_db)],
) -> CharacterKnowledgeService:
    return CharacterKnowledgeService(db)


def get_character_arc_service(db: Annotated[Session, Depends(get_db)]) -> CharacterArcService:
    return CharacterArcService(db)


def not_found_response(error: NotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.post(
    "/universes/{universe_id}/characters",
    response_model=CharacterRead,
    status_code=status.HTTP_201_CREATED,
)
def create_character(
    universe_id: uuid.UUID,
    payload: CharacterCreate,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    try:
        return service.create(universe_id, payload)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/universes/{universe_id}/characters", response_model=list[CharacterRead])
def list_characters(
    universe_id: uuid.UUID,
    service: Annotated[CharacterService, Depends(get_character_service)],
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[CharacterRead]:
    try:
        return service.list_by_universe(universe_id, limit=limit, offset=offset)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/characters/{character_id}", response_model=CharacterRead)
def get_character(
    character_id: uuid.UUID,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    try:
        return service.get(character_id)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/characters/{character_id}/memory", response_model=CharacterMemoryResponse)
def get_character_memory(
    character_id: uuid.UUID,
    service: Annotated[CharacterMemoryService, Depends(get_character_memory_service)],
) -> CharacterMemoryResponse:
    try:
        return service.get_memory(character_id)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/characters/{character_id}/knowledge", response_model=CharacterKnowledgeResponse)
def get_character_knowledge(
    character_id: uuid.UUID,
    service: Annotated[CharacterKnowledgeService, Depends(get_character_knowledge_service)],
) -> CharacterKnowledgeResponse:
    try:
        return CharacterKnowledgeResponse(
            character_id=character_id,
            knowledge=service.get_knowledge(character_id),
        )
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/characters/{character_id}/arc", response_model=CharacterArcResponse)
def get_character_arc(
    character_id: uuid.UUID,
    service: Annotated[CharacterArcService, Depends(get_character_arc_service)],
) -> CharacterArcResponse:
    try:
        return CharacterArcResponse(character_id=character_id, arc=service.get_arc(character_id))
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get(
    "/characters/{character_id}/relationships",
    response_model=CharacterRelationshipResponse,
)
def get_character_relationships(
    character_id: uuid.UUID,
    service: Annotated[CharacterMemoryService, Depends(get_character_memory_service)],
) -> CharacterRelationshipResponse:
    try:
        return CharacterRelationshipResponse(
            character_id=character_id,
            relationships=service.get_relationships(character_id),
        )
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/characters/{character_id}/state", response_model=CharacterStateResponse)
def get_character_state(
    character_id: uuid.UUID,
    service: Annotated[CharacterMemoryService, Depends(get_character_memory_service)],
) -> CharacterStateResponse:
    try:
        return service.get_state(character_id)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.get("/characters/{character_id}/context-pack", response_model=CharacterContextPack)
def get_character_context_pack(
    character_id: uuid.UUID,
    service: Annotated[CharacterMemoryService, Depends(get_character_memory_service)],
) -> CharacterContextPack:
    try:
        return service.get_context_pack(character_id)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.patch("/characters/{character_id}", response_model=CharacterRead)
def update_character(
    character_id: uuid.UUID,
    payload: CharacterUpdate,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    try:
        return service.update(character_id, payload)
    except NotFoundError as error:
        raise not_found_response(error) from error


@router.delete("/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(
    character_id: uuid.UUID,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> None:
    try:
        service.delete(character_id)
    except NotFoundError as error:
        raise not_found_response(error) from error
