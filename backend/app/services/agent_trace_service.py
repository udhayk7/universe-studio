from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.agent_run import AgentRun
from app.db.models.episode import Episode
from app.db.models.job import Job
from app.schemas.consistency import AgentTraceResponse, AgentTraceStep


class AgentTraceService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def start(
        self,
        *,
        agent_name: str,
        universe_id: uuid.UUID | None = None,
        job_id: uuid.UUID | None = None,
        episode_id: uuid.UUID | None = None,
        input_summary: str | None = None,
    ) -> AgentRun:
        agent_run = AgentRun(
            universe_id=universe_id,
            job_id=job_id,
            episode_id=episode_id,
            agent_name=agent_name,
            input_summary=input_summary,
            status="running",
            started_at=datetime.now(UTC),
        )
        self._db.add(agent_run)
        self._db.commit()
        self._db.refresh(agent_run)
        return agent_run

    def complete(
        self,
        agent_run: AgentRun,
        *,
        output_summary: str,
        episode_id: uuid.UUID | None = None,
    ) -> AgentRun:
        completed_at = datetime.now(UTC)
        agent_run.status = "completed"
        agent_run.output_summary = output_summary
        agent_run.completed_at = completed_at
        if episode_id is not None:
            agent_run.episode_id = episode_id
        if agent_run.started_at is not None:
            agent_run.duration_ms = int(
                (completed_at - agent_run.started_at).total_seconds() * 1000
            )
        self._db.add(agent_run)
        self._db.commit()
        self._db.refresh(agent_run)
        return agent_run

    def fail(self, agent_run: AgentRun, *, output_summary: str) -> AgentRun:
        completed_at = datetime.now(UTC)
        agent_run.status = "failed"
        agent_run.output_summary = output_summary
        agent_run.completed_at = completed_at
        if agent_run.started_at is not None:
            agent_run.duration_ms = int(
                (completed_at - agent_run.started_at).total_seconds() * 1000
            )
        self._db.add(agent_run)
        self._db.commit()
        self._db.refresh(agent_run)
        return agent_run

    def attach_episode_to_job_runs(
        self,
        *,
        job_id: uuid.UUID,
        episode_id: uuid.UUID,
    ) -> None:
        runs = self._db.scalars(
            select(AgentRun).where(
                AgentRun.job_id == job_id,
                AgentRun.episode_id.is_(None),
            )
        ).all()
        for run in runs:
            run.episode_id = episode_id
            self._db.add(run)
        self._db.commit()

    def get_episode_trace(self, episode_id: uuid.UUID) -> AgentTraceResponse:
        episode = self._db.get(Episode, episode_id)
        if episode is None:
            raise NotFoundError("Episode", episode_id)

        runs = self._db.scalars(
            select(AgentRun)
            .where(AgentRun.episode_id == episode_id)
            .order_by(AgentRun.started_at.asc().nulls_last(), AgentRun.created_at.asc())
        ).all()
        return AgentTraceResponse(
            episode_id=episode_id,
            steps=[AgentTraceStep.model_validate(run) for run in runs],
        )

    def get_job_trace(self, job_id: uuid.UUID) -> AgentTraceResponse:
        job = self._db.get(Job, job_id)
        if job is None:
            raise NotFoundError("Job", job_id)

        runs = self._db.scalars(
            select(AgentRun)
            .where(AgentRun.job_id == job_id)
            .order_by(AgentRun.started_at.asc().nulls_last(), AgentRun.created_at.asc())
        ).all()
        return AgentTraceResponse(
            job_id=job_id,
            steps=[AgentTraceStep.model_validate(run) for run in runs],
        )
