from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse
from app.schemas.episode_generation import EpisodeParticipantRead


class StoryboardRenderRequest(BaseModel):
    regenerate_images: bool = False


class StoryboardImageRead(TimestampedResponse):
    episode_id: uuid.UUID
    scene_id: uuid.UUID
    shot_id: uuid.UUID
    provider: str
    model: str | None = None
    status: str
    mime_type: str | None = None
    image_data: str | None = None
    image_url: str | None = None
    prompt: str
    revised_prompt: str | None = None
    width: int | None = None
    height: int | None = None
    error: str | None = None
    generated_at: datetime | None = None


class ShotRead(TimestampedResponse):
    episode_id: uuid.UUID
    scene_id: uuid.UUID
    scene_number: int
    scene_title: str | None = None
    shot_number: int
    shot_type: str
    camera_angle: str
    duration_seconds: float
    visual_description: str
    prompt: str | None = None
    status: str
    storyboard_image: StoryboardImageRead | None = None


class StoryboardSceneRead(BaseModel):
    scene_id: uuid.UUID
    scene_number: int
    title: str | None = None
    location_name: str | None = None
    summary: str | None = None
    visual_direction: str | None = None
    participants: list[EpisodeParticipantRead] = Field(default_factory=list)
    shots: list[ShotRead] = Field(default_factory=list)


class EpisodeStoryboardRead(BaseModel):
    episode_id: uuid.UUID
    universe_id: uuid.UUID
    title: str
    summary: str | None = None
    scene_count: int
    shot_count: int
    generated_image_count: int
    scenes: list[StoryboardSceneRead] = Field(default_factory=list)
