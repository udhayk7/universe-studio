from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.timeline import Timeline
from app.repositories.timeline_repository import TimelineRepository
from app.repositories.universe_repository import UniverseRepository
from app.schemas.timeline import TimelineCreate, TimelineUpdate


class TimelineService:
    def __init__(self, db: Session) -> None:
        self._timeline_repository = TimelineRepository(db)
        self._universe_repository = UniverseRepository(db)

    def create(self, universe_id: uuid.UUID, payload: TimelineCreate) -> Timeline:
        if self._universe_repository.get(universe_id) is None:
            raise NotFoundError("Universe", universe_id)
        return self._timeline_repository.create(universe_id, payload.model_dump())

    def list_by_universe(
        self, universe_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[Timeline]:
        if self._universe_repository.get(universe_id) is None:
            raise NotFoundError("Universe", universe_id)
        return self._timeline_repository.list_by_universe(universe_id, limit=limit, offset=offset)

    def get(self, timeline_id: uuid.UUID) -> Timeline:
        timeline = self._timeline_repository.get(timeline_id)
        if timeline is None:
            raise NotFoundError("Timeline", timeline_id)
        return timeline

    def update(self, timeline_id: uuid.UUID, payload: TimelineUpdate) -> Timeline:
        timeline = self.get(timeline_id)
        return self._timeline_repository.update(timeline, payload.model_dump(exclude_unset=True))

    def delete(self, timeline_id: uuid.UUID) -> None:
        timeline = self.get(timeline_id)
        self._timeline_repository.delete(timeline)
