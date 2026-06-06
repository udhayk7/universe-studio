from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse


class CharacterCreate(BaseModel):
    canonical_name: str = Field(min_length=1, max_length=255)
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    traits: dict[str, Any] = Field(default_factory=dict)
    goals: dict[str, Any] = Field(default_factory=dict)
    fears: dict[str, Any] = Field(default_factory=dict)
    voice_style: str | None = None
    status: str = Field(default="unknown", max_length=50)


class CharacterUpdate(BaseModel):
    canonical_name: str | None = Field(default=None, min_length=1, max_length=255)
    aliases: list[str] | None = None
    description: str | None = None
    traits: dict[str, Any] | None = None
    goals: dict[str, Any] | None = None
    fears: dict[str, Any] | None = None
    voice_style: str | None = None
    status: str | None = Field(default=None, max_length=50)


class CharacterRead(TimestampedResponse):
    universe_id: uuid.UUID
    canonical_name: str
    aliases: list[str]
    description: str | None = None
    traits: dict[str, Any]
    goals: dict[str, Any]
    fears: dict[str, Any]
    voice_style: str | None = None
    status: str
