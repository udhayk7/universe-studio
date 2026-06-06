from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


def _strip_text(value: str) -> str:
    return value.strip()


class ExtractedUniverse(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    premise: str = Field(min_length=1)
    genre: str = Field(min_length=1, max_length=100)
    tone: str = Field(min_length=1, max_length=100)
    world_rules: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("title", "premise", "genre", "tone")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return _strip_text(value)


class ExtractedCharacter(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    personality: list[str] = Field(default_factory=list, max_length=12)
    goals: list[str] = Field(default_factory=list, max_length=8)
    fears: list[str] = Field(default_factory=list, max_length=8)
    current_status: str = Field(default="unknown", max_length=50)

    @field_validator("name", "description", "current_status")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class ExtractedLocation(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    type: str = Field(default="location", max_length=100)

    @field_validator("name", "description", "type")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class ExtractedObject(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    importance: str = Field(min_length=1, max_length=100)

    @field_validator("name", "description", "importance")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class ExtractedEvent(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1)
    participants: list[str] = Field(default_factory=list, max_length=12)
    location: str | None = Field(default=None, max_length=255)
    importance: int = Field(ge=1, le=10)

    @field_validator("title", "summary")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        return _strip_text(value)


class ExtractedRelationship(BaseModel):
    source_character: str = Field(min_length=1, max_length=255)
    target_character: str = Field(min_length=1, max_length=255)
    type: str = Field(min_length=1, max_length=100)
    strength: int = Field(ge=-100, le=100)

    @field_validator("type")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "_")

    @field_validator("source_character", "target_character")
    @classmethod
    def strip_character_names(cls, value: str) -> str:
        return _strip_text(value)


class UniverseExtraction(BaseModel):
    universe: ExtractedUniverse
    characters: list[ExtractedCharacter] = Field(default_factory=list, min_length=1, max_length=20)
    locations: list[ExtractedLocation] = Field(default_factory=list, min_length=1, max_length=20)
    objects: list[ExtractedObject] = Field(default_factory=list, min_length=1, max_length=20)
    events: list[ExtractedEvent] = Field(default_factory=list, min_length=1, max_length=30)
    relationships: list[ExtractedRelationship] = Field(
        default_factory=list,
        min_length=1,
        max_length=40,
    )


class ExtractionInput(BaseModel):
    source_type: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1)
    title_hint: str | None = Field(default=None, max_length=255)
    genre_hint: str | None = Field(default=None, max_length=100)
    tone_hint: str | None = Field(default=None, max_length=100)
