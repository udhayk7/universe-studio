from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.character import CharacterRead
from app.schemas.common import ORMModel, TimestampedResponse


class CharacterMemoryEntryRead(TimestampedResponse):
    universe_id: uuid.UUID
    timeline_id: uuid.UUID
    commit_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID | None = None
    memory_type: str
    content: str
    structured_value: dict[str, Any]
    confidence: float | None = None
    source: str
    valid_from_event_id: uuid.UUID | None = None
    valid_to_event_id: uuid.UUID | None = None


class CharacterRelationshipRead(TimestampedResponse):
    universe_id: uuid.UUID
    timeline_id: uuid.UUID
    source_character_id: uuid.UUID
    source_character_name: str
    target_character_id: uuid.UUID
    target_character_name: str
    direction: str
    relationship_type: str
    strength: int | None = None
    status: str
    evidence: str | None = None
    confidence: float | None = None


class CharacterStateHistoryRead(TimestampedResponse):
    universe_id: uuid.UUID
    character_id: uuid.UUID
    timeline_id: uuid.UUID
    commit_id: uuid.UUID
    location_id: uuid.UUID | None = None
    current_status: str
    emotional_state: str | None = None
    physical_state: str | None = None
    summary: str | None = None
    source: str
    confidence: float | None = None


class CharacterStateRead(ORMModel):
    current_status: str
    emotional_state: str | None = None
    physical_state: str | None = None
    summary: str | None = None
    source: str | None = None
    updated_at: datetime | None = None


class CharacterStateResponse(BaseModel):
    character_id: uuid.UUID
    latest: CharacterStateRead
    history: list[CharacterStateHistoryRead]


class CharacterArcEventRead(BaseModel):
    event_id: uuid.UUID
    title: str
    summary: str | None = None
    importance: int | None = None
    order_index: int | None = None
    location_name: str | None = None
    memory_id: uuid.UUID | None = None
    source: str
    created_at: datetime | None = None


class CharacterMemoryResponse(BaseModel):
    character: CharacterRead
    identity: dict[str, Any]
    personality: dict[str, Any]
    motivations: dict[str, Any]
    important_memories: list[CharacterMemoryEntryRead]


class CharacterKnowledgeResponse(BaseModel):
    character_id: uuid.UUID
    knowledge: list[CharacterMemoryEntryRead]


class CharacterArcResponse(BaseModel):
    character_id: uuid.UUID
    arc: list[CharacterArcEventRead]


class CharacterRelationshipResponse(BaseModel):
    character_id: uuid.UUID
    relationships: list[CharacterRelationshipRead]


class CharacterContextPack(BaseModel):
    character: CharacterRead
    goals: list[str]
    fears: list[str]
    traits: list[str]
    relationships: list[CharacterRelationshipRead]
    important_memories: list[CharacterMemoryEntryRead]
    knowledge: list[CharacterMemoryEntryRead]
    emotional_state: str | None = None
    current_status: str
    arc: list[CharacterArcEventRead]
