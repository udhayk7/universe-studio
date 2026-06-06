from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.db.models.character import Character
from app.db.models.character_state_history import CharacterStateHistory
from app.db.models.memory_entry import MemoryEntry
from app.db.models.relationship import Relationship
from app.schemas.character import CharacterRead
from app.schemas.character_memory import (
    CharacterContextPack,
    CharacterMemoryResponse,
    CharacterRelationshipRead,
    CharacterStateRead,
    CharacterStateResponse,
)
from app.services.character_arc_service import CharacterArcService
from app.services.character_knowledge_service import CharacterKnowledgeService

IMPORTANT_MEMORY_TYPES = frozenset(
    {
        "character_memory",
        "personality",
        "motivation",
        "goal",
        "fear",
        "character_arc_event",
    }
)


class CharacterMemoryService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_memory(self, character_id: uuid.UUID) -> CharacterMemoryResponse:
        character = self._get_character(character_id)
        memories = self._memory_entries(character_id, IMPORTANT_MEMORY_TYPES)
        return CharacterMemoryResponse(
            character=CharacterRead.model_validate(character),
            identity=self._identity(character),
            personality=self._personality(character),
            motivations=self._motivations(character),
            important_memories=memories,
        )

    def get_relationships(self, character_id: uuid.UUID) -> list[CharacterRelationshipRead]:
        character = self._get_character(character_id)
        statement = (
            select(Relationship)
            .where(
                Relationship.universe_id == character.universe_id,
                or_(
                    Relationship.source_character_id == character_id,
                    Relationship.target_character_id == character_id,
                ),
            )
            .options(
                joinedload(Relationship.source_character),
                joinedload(Relationship.target_character),
            )
            .order_by(Relationship.created_at.desc())
        )
        return [
            self._relationship_read(relationship, character_id)
            for relationship in self._db.scalars(statement)
        ]

    def get_state(self, character_id: uuid.UUID) -> CharacterStateResponse:
        character = self._get_character(character_id)
        history = self._state_history(character_id)
        latest = history[0] if history else None
        state = (
            CharacterStateRead(
                current_status=latest.current_status,
                emotional_state=latest.emotional_state,
                physical_state=latest.physical_state,
                summary=latest.summary,
                source=latest.source,
                updated_at=latest.updated_at,
            )
            if latest
            else CharacterStateRead(
                current_status=character.status,
                emotional_state=None,
                physical_state=None,
                summary=character.description,
                source="character_profile",
                updated_at=character.updated_at,
            )
        )
        return CharacterStateResponse(character_id=character_id, latest=state, history=history)

    def get_context_pack(self, character_id: uuid.UUID) -> CharacterContextPack:
        character = self._get_character(character_id)
        memory = self.get_memory(character_id)
        knowledge = CharacterKnowledgeService(self._db).get_knowledge(character_id)
        relationships = self.get_relationships(character_id)
        state = self.get_state(character_id).latest
        arc = CharacterArcService(self._db).get_arc(character_id)

        return CharacterContextPack(
            character=CharacterRead.model_validate(character),
            goals=self._list_from_payload(character.goals),
            fears=self._list_from_payload(character.fears),
            traits=self._list_from_payload(character.traits, preferred_key="personality"),
            relationships=relationships,
            important_memories=memory.important_memories,
            knowledge=knowledge,
            emotional_state=state.emotional_state,
            current_status=state.current_status,
            arc=arc,
        )

    def _memory_entries(
        self,
        character_id: uuid.UUID,
        memory_types: frozenset[str],
    ) -> list[MemoryEntry]:
        statement = (
            select(MemoryEntry)
            .where(
                MemoryEntry.entity_type == "character",
                MemoryEntry.entity_id == character_id,
                MemoryEntry.memory_type.in_(memory_types),
            )
            .order_by(MemoryEntry.created_at.desc())
        )
        return list(self._db.scalars(statement))

    def _state_history(self, character_id: uuid.UUID) -> list[CharacterStateHistory]:
        statement = (
            select(CharacterStateHistory)
            .where(CharacterStateHistory.character_id == character_id)
            .order_by(CharacterStateHistory.created_at.desc())
        )
        return list(self._db.scalars(statement))

    def _relationship_read(
        self,
        relationship: Relationship,
        character_id: uuid.UUID,
    ) -> CharacterRelationshipRead:
        direction = "outgoing" if relationship.source_character_id == character_id else "incoming"
        return CharacterRelationshipRead(
            id=relationship.id,
            created_at=relationship.created_at,
            updated_at=relationship.updated_at,
            universe_id=relationship.universe_id,
            timeline_id=relationship.timeline_id,
            source_character_id=relationship.source_character_id,
            source_character_name=relationship.source_character.canonical_name,
            target_character_id=relationship.target_character_id,
            target_character_name=relationship.target_character.canonical_name,
            direction=direction,
            relationship_type=relationship.relationship_type,
            strength=relationship.strength,
            status=relationship.status,
            evidence=relationship.evidence,
            confidence=relationship.confidence,
        )

    def _identity(self, character: Character) -> dict[str, Any]:
        return {
            "name": character.canonical_name,
            "aliases": character.aliases,
            "description": character.description,
            "status": character.status,
        }

    def _personality(self, character: Character) -> dict[str, Any]:
        return {
            "traits": self._list_from_payload(character.traits, preferred_key="personality"),
            "strengths": self._list_from_payload(character.traits, preferred_key="strengths"),
            "weaknesses": self._list_from_payload(character.traits, preferred_key="weaknesses"),
        }

    def _motivations(self, character: Character) -> dict[str, Any]:
        return {
            "goals": self._list_from_payload(character.goals),
            "fears": self._list_from_payload(character.fears),
        }

    def _list_from_payload(
        self,
        payload: dict[str, Any],
        *,
        preferred_key: str = "items",
    ) -> list[str]:
        value = payload.get(preferred_key) or payload.get("items") or []
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    def _get_character(self, character_id: uuid.UUID) -> Character:
        character = self._db.get(Character, character_id)
        if character is None:
            raise NotFoundError("Character", character_id)
        return character
