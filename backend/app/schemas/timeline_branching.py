from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import TimestampedResponse
from app.schemas.timeline import TimelineRead


class TimelineCommitRead(TimestampedResponse):
    timeline_id: uuid.UUID
    parent_commit_id: uuid.UUID | None = None
    message: str
    commit_type: str
    created_by: str


class TimelineEventRead(TimestampedResponse):
    title: str
    summary: str | None = None
    event_type: str | None = None
    order_index: int | None = None
    importance: int | None = None
    location_id: uuid.UUID | None = None
    location_name: str | None = None
    participants: list[str] = Field(default_factory=list)
    commit_id: uuid.UUID | None = None
    commit_message: str | None = None
    commit_type: str | None = None
    change_type: str | None = None


class TimelineBranchCreate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    event_id: uuid.UUID | None = None
    commit_id: uuid.UUID | None = None
    modified_title: str | None = Field(default=None, max_length=255)
    new_outcome: str = Field(min_length=1, max_length=4_000)

    @model_validator(mode="after")
    def validate_branch_point(self) -> TimelineBranchCreate:
        if self.event_id is None and self.commit_id is None:
            raise ValueError("event_id or commit_id is required to create a branch.")
        return self


class TimelineImpactAnalysis(BaseModel):
    alternate_history_summary: str = Field(min_length=1)
    impacted_characters: list[str] = Field(default_factory=list, max_length=12)
    impacted_relationships: list[str] = Field(default_factory=list, max_length=12)
    impacted_events: list[str] = Field(default_factory=list, max_length=12)
    memory_updates: list[str] = Field(default_factory=list, max_length=12)


class TimelineBranchRead(BaseModel):
    timeline: TimelineRead
    branch_commit: TimelineCommitRead
    modified_event: TimelineEventRead
    impact: TimelineImpactAnalysis


class TimelineDiffEvent(BaseModel):
    kind: str
    title: str
    base_summary: str | None = None
    compare_summary: str | None = None
    order_index: int | None = None


class TimelineDiffRelationship(BaseModel):
    source_character: str
    target_character: str
    relationship_type: str
    base_strength: int | None = None
    compare_strength: int | None = None
    base_status: str | None = None
    compare_status: str | None = None


class TimelineDiffState(BaseModel):
    character: str
    base_status: str | None = None
    compare_status: str | None = None
    base_emotional_state: str | None = None
    compare_emotional_state: str | None = None
    base_summary: str | None = None
    compare_summary: str | None = None


class TimelineDiffResponse(BaseModel):
    base_timeline_id: uuid.UUID
    compare_timeline_id: uuid.UUID
    base_timeline_name: str
    compare_timeline_name: str
    changed_events: list[TimelineDiffEvent] = Field(default_factory=list)
    relationship_differences: list[TimelineDiffRelationship] = Field(default_factory=list)
    state_differences: list[TimelineDiffState] = Field(default_factory=list)


class FutureGenerateRequest(BaseModel):
    prompt: str | None = Field(default=None, max_length=2_000)


class FutureGenerateResponse(BaseModel):
    job_id: uuid.UUID
    timeline_id: uuid.UUID
    universe_id: uuid.UUID
    status: str
    progress: int
    message: str | None = None
    created_at: datetime
