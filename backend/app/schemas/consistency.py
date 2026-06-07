from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import TimestampedResponse

ConsistencySeverity = Literal["low", "medium", "high", "blocker"]
ConsistencyStatus = Literal["open", "resolved", "ignored"]


class AffectedEntity(BaseModel):
    entity_type: str = Field(min_length=1, max_length=100)
    entity_id: str | None = Field(default=None, max_length=100)
    name: str | None = Field(default=None, max_length=255)


class ConsistencyIssue(BaseModel):
    severity: ConsistencySeverity
    issue_type: str = Field(min_length=1, max_length=100)
    issue: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    suggested_fix: str | None = None
    affected_entities: list[AffectedEntity] = Field(default_factory=list, max_length=12)

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, value: str) -> str:
        normalized = value.strip().casefold()
        if normalized == "critical":
            return "blocker"
        return normalized


class ConsistencyReport(BaseModel):
    verdict: Literal["pass", "warning", "fail"]
    issues: list[ConsistencyIssue] = Field(default_factory=list, max_length=30)
    summary: str = Field(min_length=1)


class ConsistencyCheckRequest(BaseModel):
    episode_id: uuid.UUID | None = None
    universe_id: uuid.UUID
    timeline_id: uuid.UUID
    content: str = Field(min_length=1)


class ConsistencyCheckRead(TimestampedResponse):
    universe_id: uuid.UUID
    timeline_id: uuid.UUID
    episode_id: uuid.UUID | None = None
    severity: str
    issue_type: str
    description: str
    suggested_fix: str | None = None
    affected_entities: list[dict[str, object]] = Field(default_factory=list)
    status: str


class ConsistencyCheckResult(BaseModel):
    report: ConsistencyReport
    checks: list[ConsistencyCheckRead] = Field(default_factory=list)


class ConsistencyDashboardSummary(BaseModel):
    universe_id: uuid.UUID
    open_issues: int
    resolved_issues: int
    severity_breakdown: dict[str, int]
    timeline_conflicts: int
    character_conflicts: int
    relationship_conflicts: int
    world_rule_violations: int
    branch_conflicts: int
    issues: list[ConsistencyCheckRead] = Field(default_factory=list)


class AgentTraceStep(TimestampedResponse):
    universe_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None
    episode_id: uuid.UUID | None = None
    agent_name: str
    input_summary: str | None = None
    output_summary: str | None = None
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None


class AgentTraceResponse(BaseModel):
    trace_id: uuid.UUID | None = None
    episode_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None
    steps: list[AgentTraceStep] = Field(default_factory=list)
