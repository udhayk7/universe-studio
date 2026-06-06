from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.character import Character
from app.db.models.memory_entry import MemoryEntry

KNOWLEDGE_MEMORY_TYPES = frozenset({"knowledge", "secret", "personal_memory"})


class CharacterKnowledgeService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_knowledge(self, character_id: uuid.UUID) -> list[MemoryEntry]:
        self._get_character(character_id)
        statement = (
            select(MemoryEntry)
            .where(
                MemoryEntry.entity_type == "character",
                MemoryEntry.entity_id == character_id,
                MemoryEntry.memory_type.in_(KNOWLEDGE_MEMORY_TYPES),
            )
            .order_by(MemoryEntry.created_at.desc())
        )
        return list(self._db.scalars(statement))

    def _get_character(self, character_id: uuid.UUID) -> Character:
        character = self._db.get(Character, character_id)
        if character is None:
            raise NotFoundError("Character", character_id)
        return character
