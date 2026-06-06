from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import TimestampedResponse


def _strip_text(value: str) -> str:
    return value.strip()


class EpisodeGenerateRequest(BaseModel):
    prompt: str | None = Field(default=None, max_length=2_000)

    @field_validator("prompt")
    @classmethod
    def strip_prompt(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class EpisodeContextUniverse(BaseModel):
    id: str
    title: str
    premise: str | None = None
    genre: str | None = None
    tone: str | None = None


class EpisodeContextCharacter(BaseModel):
    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    status: str
    traits: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    fears: list[str] = Field(default_factory=list)
    emotional_state: str | None = None
    recent_memories: list[str] = Field(default_factory=list)
    knowledge: list[str] = Field(default_factory=list)


class EpisodeContextRelationship(BaseModel):
    source_character: str
    target_character: str
    relationship_type: str
    strength: int | None = None
    status: str
    evidence: str | None = None


class EpisodeContextEvent(BaseModel):
    title: str
    summary: str | None = None
    order_index: int | None = None
    importance: int | None = None
    location: str | None = None
    participants: list[str] = Field(default_factory=list)


class EpisodeContextLocation(BaseModel):
    id: str
    name: str
    description: str | None = None
    location_type: str | None = None


class EpisodeContextObject(BaseModel):
    id: str
    name: str
    description: str | None = None
    object_type: str | None = None
    status: str
    owner: str | None = None
    location: str | None = None


class EpisodeContextPack(BaseModel):
    universe: EpisodeContextUniverse
    timeline_id: str
    timeline_name: str
    request_prompt: str | None = None
    world_rules: list[str] = Field(default_factory=list)
    characters: list[EpisodeContextCharacter] = Field(default_factory=list)
    relationships: list[EpisodeContextRelationship] = Field(default_factory=list)
    events: list[EpisodeContextEvent] = Field(default_factory=list)
    locations: list[EpisodeContextLocation] = Field(default_factory=list)
    objects: list[EpisodeContextObject] = Field(default_factory=list)
    memory_entries: list[str] = Field(default_factory=list)


class EpisodeBeat(BaseModel):
    beat_number: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1)
    characters: list[str] = Field(default_factory=list, min_length=1, max_length=8)
    location: str = Field(min_length=1, max_length=255)
    emotional_turn: str = Field(min_length=1)

    @field_validator("title", "summary", "location", "emotional_turn")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class CharacterDevelopmentNote(BaseModel):
    character: str = Field(min_length=1, max_length=255)
    starting_state: str = Field(min_length=1)
    pressure: str = Field(min_length=1)
    ending_shift: str = Field(min_length=1)

    @field_validator("character", "starting_state", "pressure", "ending_shift")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class EpisodeOutline(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    logline: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    beats: list[EpisodeBeat] = Field(default_factory=list, min_length=3, max_length=8)
    character_development: list[CharacterDevelopmentNote] = Field(
        default_factory=list,
        min_length=1,
        max_length=8,
    )
    continuity_references: list[str] = Field(default_factory=list, min_length=3, max_length=12)

    @field_validator("title", "logline", "summary")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class GeneratedDialogueLine(BaseModel):
    character: str = Field(min_length=1, max_length=255)
    line: str = Field(min_length=1)

    @field_validator("character", "line")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class GeneratedScene(BaseModel):
    scene_number: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=255)
    characters: list[str] = Field(default_factory=list, min_length=1, max_length=10)
    description: str = Field(min_length=1)
    dialogue: list[GeneratedDialogueLine] = Field(default_factory=list, min_length=2, max_length=24)
    outcome: str = Field(min_length=1)
    memory_implications: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("title", "location", "description", "outcome")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class GeneratedRelationshipChange(BaseModel):
    source_character: str = Field(min_length=1, max_length=255)
    target_character: str = Field(min_length=1, max_length=255)
    relationship_type: str = Field(min_length=1, max_length=100)
    strength_delta: int = Field(ge=-100, le=100)
    rationale: str = Field(min_length=1)

    @field_validator("relationship_type")
    @classmethod
    def normalize_relationship_type(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "_")

    @field_validator("source_character", "target_character", "rationale")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class GeneratedCharacterStateChange(BaseModel):
    character: str = Field(min_length=1, max_length=255)
    current_status: str = Field(min_length=1, max_length=50)
    emotional_state: str = Field(min_length=1, max_length=100)
    physical_state: str | None = Field(default=None, max_length=100)
    summary: str = Field(min_length=1)

    @field_validator("character", "current_status", "emotional_state", "summary")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class GeneratedKnowledgeChange(BaseModel):
    character: str = Field(min_length=1, max_length=255)
    knowledge: str = Field(min_length=1)
    secrecy_level: str = Field(default="personal", max_length=100)
    source_scene_number: int | None = Field(default=None, ge=1)

    @field_validator("character", "knowledge", "secrecy_level")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class GeneratedEventMemory(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1)
    importance: int = Field(ge=1, le=10)
    scene_number: int | None = Field(default=None, ge=1)
    participants: list[str] = Field(default_factory=list, max_length=10)
    location: str | None = Field(default=None, max_length=255)

    @field_validator("title", "summary")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class GeneratedEpisode(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1)
    scenes: list[GeneratedScene] = Field(default_factory=list, min_length=3, max_length=8)
    relationship_changes: list[GeneratedRelationshipChange] = Field(
        default_factory=list,
        max_length=12,
    )
    character_state_changes: list[GeneratedCharacterStateChange] = Field(
        default_factory=list,
        max_length=12,
    )
    knowledge_changes: list[GeneratedKnowledgeChange] = Field(default_factory=list, max_length=16)
    new_event_memories: list[GeneratedEventMemory] = Field(default_factory=list, max_length=10)

    @field_validator("title", "summary")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class EpisodeParticipantRead(BaseModel):
    character_id: uuid.UUID
    character_name: str
    role: str


class EpisodeSceneRead(TimestampedResponse):
    episode_id: uuid.UUID
    location_id: uuid.UUID | None = None
    location_name: str | None = None
    scene_number: int
    title: str | None = None
    summary: str | None = None
    dialogue: str | None = None
    visual_direction: str | None = None
    participants: list[EpisodeParticipantRead] = Field(default_factory=list)


class EpisodeRead(TimestampedResponse):
    universe_id: uuid.UUID
    timeline_id: uuid.UUID
    commit_id: uuid.UUID | None = None
    title: str
    logline: str | None = None
    summary: str | None = None
    status: str
    scene_count: int = 0


class EpisodeGenerateResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    progress: int
    message: str | None = None
    episode_id: uuid.UUID | None = None
    created_at: datetime
