from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.timeline import Timeline


class TimelineRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, universe_id: uuid.UUID, values: dict[str, Any]) -> Timeline:
        timeline = Timeline(universe_id=universe_id, **values)
        self._db.add(timeline)
        self._db.commit()
        self._db.refresh(timeline)
        return timeline

    def list_by_universe(
        self, universe_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[Timeline]:
        statement = (
            select(Timeline)
            .where(Timeline.universe_id == universe_id)
            .order_by(Timeline.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._db.scalars(statement))

    def get(self, timeline_id: uuid.UUID) -> Timeline | None:
        return self._db.get(Timeline, timeline_id)

    def update(self, timeline: Timeline, values: dict[str, Any]) -> Timeline:
        for key, value in values.items():
            setattr(timeline, key, value)
        self._db.add(timeline)
        self._db.commit()
        self._db.refresh(timeline)
        return timeline

    def delete(self, timeline: Timeline) -> None:
        self._db.delete(timeline)
        self._db.commit()
