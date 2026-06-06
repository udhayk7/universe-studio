from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SourceType = Literal["idea", "script", "scene", "screenplay"]


class SourcePayload(BaseModel):
    source_type: SourceType
    content: str = Field(min_length=1)
    title_hint: str | None = Field(default=None, max_length=255)
    genre_hint: str | None = Field(default=None, max_length=100)
    tone_hint: str | None = Field(default=None, max_length=100)
    filename: str | None = Field(default=None, max_length=255)
    mime_type: str | None = Field(default=None, max_length=255)


class CreateFromInputResponse(BaseModel):
    job_id: str
    universe_id: str | None = None
    status: str
    progress: int
    message: str | None = None
