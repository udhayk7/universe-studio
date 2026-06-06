from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.job import Job


class JobService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        job_type: str,
        universe_id: uuid.UUID | None = None,
        message: str | None = None,
    ) -> Job:
        job = Job(
            universe_id=universe_id,
            job_type=job_type,
            status="queued",
            progress=0,
            message=message,
        )
        self._db.add(job)
        self._db.commit()
        self._db.refresh(job)
        return job

    def get(self, job_id: uuid.UUID) -> Job:
        job = self._db.get(Job, job_id)
        if job is None:
            raise NotFoundError("Job", job_id)
        return job

    def update(
        self,
        job_id: uuid.UUID,
        *,
        status: str | None = None,
        progress: int | None = None,
        message: str | None = None,
        universe_id: uuid.UUID | None = None,
        result_data: dict[str, Any] | None = None,
        completed: bool = False,
    ) -> Job:
        job = self.get(job_id)
        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        if message is not None:
            job.message = message
        if universe_id is not None:
            job.universe_id = universe_id
        if result_data is not None:
            job.result_data = result_data
        if completed:
            job.completed_at = datetime.now(UTC)

        self._db.add(job)
        self._db.commit()
        self._db.refresh(job)
        return job
