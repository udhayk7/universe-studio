from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.character import Character


class CharacterRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, universe_id: uuid.UUID, values: dict[str, Any]) -> Character:
        character = Character(universe_id=universe_id, **values)
        self._db.add(character)
        self._db.commit()
        self._db.refresh(character)
        return character

    def list_by_universe(
        self, universe_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> list[Character]:
        statement = (
            select(Character)
            .where(Character.universe_id == universe_id)
            .order_by(Character.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._db.scalars(statement))

    def get(self, character_id: uuid.UUID) -> Character | None:
        return self._db.get(Character, character_id)

    def update(self, character: Character, values: dict[str, Any]) -> Character:
        for key, value in values.items():
            setattr(character, key, value)
        self._db.add(character)
        self._db.commit()
        self._db.refresh(character)
        return character

    def delete(self, character: Character) -> None:
        self._db.delete(character)
        self._db.commit()
