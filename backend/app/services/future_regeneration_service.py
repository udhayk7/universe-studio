from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.job import Job
from app.db.models.timeline import Timeline
from app.services.job_service import JobService


class FutureRegenerationService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._job_service = JobService(db)

    def create_generation_job(self, timeline_id: uuid.UUID) -> Job:
        timeline = self._db.get(Timeline, timeline_id)
        if timeline is None:
            raise NotFoundError("Timeline", timeline_id)

        return self._job_service.create(
            job_type="alternate_future_generation",
            universe_id=timeline.universe_id,
            message=f"Alternate future queued for {timeline.name}",
        )
