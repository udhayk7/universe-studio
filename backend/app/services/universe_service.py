from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.universe import Universe
from app.repositories.universe_repository import UniverseRepository
from app.schemas.universe import UniverseCreate, UniverseUpdate


class UniverseService:
    def __init__(self, db: Session) -> None:
        self._repository = UniverseRepository(db)

    def create(self, payload: UniverseCreate) -> Universe:
        return self._repository.create(payload.model_dump())

    def list(self, limit: int = 100, offset: int = 0) -> list[Universe]:
        return self._repository.list(limit=limit, offset=offset)

    def get(self, universe_id: uuid.UUID) -> Universe:
        universe = self._repository.get(universe_id)
        if universe is None:
            raise NotFoundError("Universe", universe_id)
        return universe

    def update(self, universe_id: uuid.UUID, payload: UniverseUpdate) -> Universe:
        universe = self.get(universe_id)
        return self._repository.update(universe, payload.model_dump(exclude_unset=True))

    def delete(self, universe_id: uuid.UUID) -> None:
        universe = self.get(universe_id)
        self._repository.delete(universe)
