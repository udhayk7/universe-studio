from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse


class TimelineCreate(BaseModel):
    parent_timeline_id: uuid.UUID | None = None
    branch_from_commit_id: uuid.UUID | None = None
    head_commit_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    is_canon: bool = False


class TimelineUpdate(BaseModel):
    parent_timeline_id: uuid.UUID | None = None
    branch_from_commit_id: uuid.UUID | None = None
    head_commit_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_canon: bool | None = None


class TimelineRead(TimestampedResponse):
    universe_id: uuid.UUID
    parent_timeline_id: uuid.UUID | None = None
    branch_from_commit_id: uuid.UUID | None = None
    head_commit_id: uuid.UUID | None = None
    name: str
    is_canon: bool
