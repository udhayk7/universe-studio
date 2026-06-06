from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.universe import Universe


class UniverseRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, values: dict[str, Any]) -> Universe:
        universe = Universe(**values)
        self._db.add(universe)
        self._db.commit()
        self._db.refresh(universe)
        return universe

    def list(self, limit: int = 100, offset: int = 0) -> list[Universe]:
        statement = (
            select(Universe).order_by(Universe.created_at.desc()).limit(limit).offset(offset)
        )
        return list(self._db.scalars(statement))

    def get(self, universe_id: uuid.UUID) -> Universe | None:
        return self._db.get(Universe, universe_id)

    def update(self, universe: Universe, values: dict[str, Any]) -> Universe:
        for key, value in values.items():
            setattr(universe, key, value)
        self._db.add(universe)
        self._db.commit()
        self._db.refresh(universe)
        return universe

    def delete(self, universe: Universe) -> None:
        self._db.delete(universe)
        self._db.commit()
