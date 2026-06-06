from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse


class UniverseBase(TimestampedResponse):
    owner_id: uuid.UUID | None = None
    active_timeline_id: uuid.UUID | None = None
    title: str
    tagline: str | None = None
    premise: str | None = None
    genre: str | None = None
    tone: str | None = None
    status: str


class UniverseCreate(BaseModel):
    owner_id: uuid.UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    tagline: str | None = Field(default=None, max_length=500)
    premise: str | None = None
    genre: str | None = Field(default=None, max_length=100)
    tone: str | None = Field(default=None, max_length=100)
    status: str = Field(default="draft", max_length=50)


class UniverseUpdate(BaseModel):
    owner_id: uuid.UUID | None = None
    active_timeline_id: uuid.UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    tagline: str | None = Field(default=None, max_length=500)
    premise: str | None = None
    genre: str | None = Field(default=None, max_length=100)
    tone: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=50)


class UniverseRead(UniverseBase):
    pass
