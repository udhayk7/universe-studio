from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.db.models.character import Character
from app.db.models.event import Event
from app.db.models.event_participant import EventParticipant
from app.db.models.memory_entry import MemoryEntry
from app.schemas.character_memory import CharacterArcEventRead


class CharacterArcService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_arc(self, character_id: uuid.UUID) -> list[CharacterArcEventRead]:
        self._get_character(character_id)
        arc_events = self._event_arc(character_id)
        memory_events = self._memory_arc(character_id)

        seen_event_ids = {event.event_id for event in arc_events}
        merged = [
            *arc_events,
            *(event for event in memory_events if event.event_id not in seen_event_ids),
        ]
        return sorted(
            merged,
            key=lambda event: (
                event.order_index if event.order_index is not None else 10_000,
                event.created_at.isoformat() if event.created_at else "",
            ),
        )

    def _event_arc(self, character_id: uuid.UUID) -> list[CharacterArcEventRead]:
        statement = (
            select(EventParticipant)
            .where(EventParticipant.character_id == character_id)
            .options(
                joinedload(EventParticipant.event).joinedload(Event.location),
            )
            .order_by(EventParticipant.created_at.asc())
        )
        arc: list[CharacterArcEventRead] = []
        for participant in self._db.scalars(statement):
            event = participant.event
            arc.append(
                CharacterArcEventRead(
                    event_id=event.id,
                    title=event.title,
                    summary=event.summary,
                    importance=event.importance,
                    order_index=event.order_index,
                    location_name=event.location.name if event.location else None,
                    memory_id=None,
                    source="event_participation",
                    created_at=event.created_at,
                )
            )
        return arc

    def _memory_arc(self, character_id: uuid.UUID) -> list[CharacterArcEventRead]:
        statement = (
            select(MemoryEntry)
            .where(
                MemoryEntry.entity_type == "character",
                MemoryEntry.entity_id == character_id,
                MemoryEntry.memory_type == "character_arc_event",
                MemoryEntry.valid_from_event_id.is_not(None),
            )
            .order_by(MemoryEntry.created_at.asc())
        )
        arc: list[CharacterArcEventRead] = []
        for memory in self._db.scalars(statement):
            if memory.valid_from_event_id is None:
                continue
            arc.append(
                CharacterArcEventRead(
                    event_id=memory.valid_from_event_id,
                    title=memory.structured_value.get("event_title", "Character arc event"),
                    summary=memory.content,
                    importance=memory.structured_value.get("importance"),
                    order_index=memory.structured_value.get("order_index"),
                    location_name=memory.structured_value.get("location_name"),
                    memory_id=memory.id,
                    source=memory.source,
                    created_at=memory.created_at,
                )
            )
        return arc

    def _get_character(self, character_id: uuid.UUID) -> Character:
        character = self._db.get(Character, character_id)
        if character is None:
            raise NotFoundError("Character", character_id)
        return character
