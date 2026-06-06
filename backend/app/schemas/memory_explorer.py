from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel

MemoryNodeType = Literal["character", "event", "location", "object"]


class UniverseMemoryStats(BaseModel):
    characters: int
    locations: int
    events: int
    objects: int
    relationships: int
    memory_entries: int
    timelines: int


class UniverseMemoryOverview(BaseModel):
    universe_id: uuid.UUID
    stats: UniverseMemoryStats


class MemoryGraphNode(BaseModel):
    id: str
    type: MemoryNodeType
    label: str
    subtitle: str | None = None
    properties: dict[str, Any]


class MemoryGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    label: str
    strength: int | None = None
    properties: dict[str, Any]


class UniverseGraphResponse(BaseModel):
    universe_id: uuid.UUID
    source: str
    nodes: list[MemoryGraphNode]
    edges: list[MemoryGraphEdge]
    warnings: list[str] = []


class MemoryParticipant(BaseModel):
    id: uuid.UUID
    name: str


class MemoryEventRead(BaseModel):
    id: uuid.UUID
    title: str
    summary: str | None = None
    importance: int | None = None
    order_index: int | None = None
    location_id: uuid.UUID | None = None
    location_name: str | None = None
    participants: list[MemoryParticipant]


class MemoryRelationshipRead(BaseModel):
    id: uuid.UUID
    source_character_id: uuid.UUID
    source_character_name: str
    target_character_id: uuid.UUID
    target_character_name: str
    relationship_type: str
    strength: int | None = None
    status: str
    evidence: str | None = None


class MemoryLocationRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    location_type: str | None = None


class MemoryObjectRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    object_type: str | None = None
    status: str
    current_owner_character_id: uuid.UUID | None = None
    current_location_id: uuid.UUID | None = None
