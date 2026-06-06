from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class DemoSeedRequest(BaseModel):
    reset: bool = True
    sync_neo4j: bool = True


class DemoSeedSummary(BaseModel):
    characters: int
    locations: int
    objects: int
    relationships: int
    events: int
    memory_entries: int
    timelines: int
    episodes: int
    scenes: int
    agent_runs: int
    consistency_checks: int


class DemoSeedResult(BaseModel):
    universe_id: uuid.UUID
    timeline_a_id: uuid.UUID
    timeline_b_id: uuid.UUID
    timeline_a_name: str = "Timeline A - Maya Survives"
    timeline_b_name: str = "Timeline B - Maya Dies"
    episode_ids: list[uuid.UUID] = Field(default_factory=list)
    branch_event_id: uuid.UUID
    alternate_future_episode_id: uuid.UUID
    summary: DemoSeedSummary
    neo4j_synced: bool
    neo4j_message: str | None = None
