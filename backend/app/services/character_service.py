from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.character import Character
from app.repositories.character_repository import CharacterRepository
from app.repositories.universe_repository import UniverseRepository
from app.schemas.character import CharacterCreate, CharacterUpdate


class CharacterService:
    def __init__(self, db: Session) -> None:
        self._character_repository = CharacterRepository(db)
        self._universe_repository = UniverseRepository(db)

    def create(self, universe_id: uuid.UUID, payload: CharacterCreate) -> Character:
        if self._universe_repository.get(universe_id) is None:
            raise NotFoundError("Universe", universe_id)
        return self._character_repository.create(universe_id, payload.model_dump())

    def list_by_universe(
        self, universe_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[Character]:
        if self._universe_repository.get(universe_id) is None:
            raise NotFoundError("Universe", universe_id)
        return self._character_repository.list_by_universe(universe_id, limit=limit, offset=offset)

    def get(self, character_id: uuid.UUID) -> Character:
        character = self._character_repository.get(character_id)
        if character is None:
            raise NotFoundError("Character", character_id)
        return character

    def update(self, character_id: uuid.UUID, payload: CharacterUpdate) -> Character:
        character = self.get(character_id)
        return self._character_repository.update(character, payload.model_dump(exclude_unset=True))

    def delete(self, character_id: uuid.UUID) -> None:
        character = self.get(character_id)
        self._character_repository.delete(character)
