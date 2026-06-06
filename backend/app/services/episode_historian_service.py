from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.db.models.character import Character
from app.db.models.character_state_history import CharacterStateHistory
from app.db.models.location import Location
from app.db.models.memory_entry import MemoryEntry
from app.db.models.relationship import Relationship
from app.db.models.timeline import Timeline
from app.db.models.universe import Universe
from app.db.models.world_object import WorldObject
from app.schemas.episode_generation import (
    EpisodeContextCharacter,
    EpisodeContextEvent,
    EpisodeContextLocation,
    EpisodeContextObject,
    EpisodeContextPack,
    EpisodeContextRelationship,
    EpisodeContextUniverse,
)
from app.services.timeline_history_service import TimelineHistoryService


class EpisodeHistorianService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def build_context_pack(
        self,
        *,
        universe_id: uuid.UUID,
        prompt: str | None,
        timeline_id: uuid.UUID | None = None,
    ) -> EpisodeContextPack:
        universe = self._db.get(Universe, universe_id)
        if universe is None:
            raise NotFoundError("Universe", universe_id)

        timeline = self._resolve_timeline(universe, timeline_id)
        characters = self._load_characters(universe.id, timeline.id)
        if not characters:
            raise ValueError("Episode generation requires at least one character in memory.")

        return EpisodeContextPack(
            universe=EpisodeContextUniverse(
                id=str(universe.id),
                title=universe.title,
                premise=universe.premise,
                genre=universe.genre,
                tone=universe.tone,
            ),
            timeline_id=str(timeline.id),
            timeline_name=timeline.name,
            request_prompt=prompt,
            world_rules=self._load_world_rules(universe.id, timeline.id),
            characters=characters,
            relationships=self._load_relationships(universe.id, timeline.id),
            events=self._load_events(timeline.id),
            locations=self._load_locations(universe.id),
            objects=self._load_objects(universe.id),
            memory_entries=self._load_universe_memories(universe.id, timeline.id),
        )

    def _resolve_timeline(self, universe: Universe, timeline_id: uuid.UUID | None) -> Timeline:
        if timeline_id:
            timeline = self._db.get(Timeline, timeline_id)
            if timeline is None or timeline.universe_id != universe.id:
                raise NotFoundError("Timeline", timeline_id)
            return timeline

        if universe.active_timeline_id:
            timeline = self._db.get(Timeline, universe.active_timeline_id)
            if timeline is not None:
                return timeline

        timeline = self._db.scalar(
            select(Timeline)
            .where(Timeline.universe_id == universe.id, Timeline.is_canon.is_(True))
            .limit(1)
        )
        if timeline is not None:
            return timeline

        timeline = self._db.scalar(select(Timeline).where(Timeline.universe_id == universe.id))
        if timeline is None:
            raise ValueError("Episode generation requires an active timeline.")
        return timeline

    def _load_characters(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
    ) -> list[EpisodeContextCharacter]:
        characters = self._db.scalars(
            select(Character)
            .where(Character.universe_id == universe_id)
            .order_by(Character.canonical_name)
        ).all()

        context_characters: list[EpisodeContextCharacter] = []
        for character in characters:
            latest_state = self._latest_state(character.id, timeline_id)
            context_characters.append(
                EpisodeContextCharacter(
                    id=str(character.id),
                    name=character.canonical_name,
                    aliases=character.aliases,
                    description=character.description,
                    status=latest_state.current_status if latest_state else character.status,
                    traits=self._string_items(character.traits, "personality"),
                    goals=self._string_items(character.goals, "items"),
                    fears=self._string_items(character.fears, "items"),
                    emotional_state=latest_state.emotional_state if latest_state else None,
                    recent_memories=self._character_memories(
                        character.id,
                        timeline_id,
                        excluded_types={"knowledge"},
                        limit=5,
                    ),
                    knowledge=self._character_memories(
                        character.id,
                        timeline_id,
                        memory_types={"knowledge"},
                        limit=5,
                    ),
                )
            )
        return context_characters

    def _load_relationships(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
    ) -> list[EpisodeContextRelationship]:
        relationships = self._db.scalars(
            select(Relationship)
            .where(
                Relationship.universe_id == universe_id,
                Relationship.timeline_id == timeline_id,
                Relationship.status == "active",
            )
            .options(
                joinedload(Relationship.source_character),
                joinedload(Relationship.target_character),
            )
            .order_by(Relationship.relationship_type)
        ).all()

        return [
            EpisodeContextRelationship(
                source_character=relationship.source_character.canonical_name,
                target_character=relationship.target_character.canonical_name,
                relationship_type=relationship.relationship_type,
                strength=relationship.strength,
                status=relationship.status,
                evidence=relationship.evidence,
            )
            for relationship in relationships
        ]

    def _load_events(self, timeline_id: uuid.UUID) -> list[EpisodeContextEvent]:
        timeline_events = TimelineHistoryService(self._db).events(timeline_id)[-30:]
        return [
            EpisodeContextEvent(
                title=event.title,
                summary=event.summary,
                order_index=event.order_index,
                importance=event.importance,
                location=event.location_name,
                participants=event.participants,
            )
            for event in timeline_events
        ]

    def _load_locations(self, universe_id: uuid.UUID) -> list[EpisodeContextLocation]:
        locations = self._db.scalars(
            select(Location).where(Location.universe_id == universe_id).order_by(Location.name)
        ).all()
        return [
            EpisodeContextLocation(
                id=str(location.id),
                name=location.name,
                description=location.description,
                location_type=location.location_type,
            )
            for location in locations
        ]

    def _load_objects(self, universe_id: uuid.UUID) -> list[EpisodeContextObject]:
        objects = self._db.scalars(
            select(WorldObject)
            .where(WorldObject.universe_id == universe_id)
            .options(
                joinedload(WorldObject.current_owner),
                joinedload(WorldObject.current_location),
            )
            .order_by(WorldObject.name)
        ).all()

        return [
            EpisodeContextObject(
                id=str(world_object.id),
                name=world_object.name,
                description=world_object.description,
                object_type=world_object.object_type,
                status=world_object.status,
                owner=(
                    world_object.current_owner.canonical_name
                    if world_object.current_owner
                    else None
                ),
                location=(
                    world_object.current_location.name
                    if world_object.current_location
                    else None
                ),
            )
            for world_object in objects
        ]

    def _load_world_rules(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
    ) -> list[str]:
        return [
            entry.content
            for entry in self._db.scalars(
                select(MemoryEntry)
                .where(
                    MemoryEntry.universe_id == universe_id,
                    MemoryEntry.timeline_id == timeline_id,
                    MemoryEntry.memory_type == "world_rule",
                )
                .order_by(MemoryEntry.created_at.desc())
                .limit(12)
            ).all()
        ]

    def _load_universe_memories(
        self,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
    ) -> list[str]:
        return [
            entry.content
            for entry in self._db.scalars(
                select(MemoryEntry)
                .where(
                    MemoryEntry.universe_id == universe_id,
                    MemoryEntry.timeline_id == timeline_id,
                    MemoryEntry.entity_type == "universe",
                )
                .order_by(MemoryEntry.created_at.desc())
                .limit(16)
            ).all()
            if entry.memory_type != "world_rule"
        ]

    def _latest_state(
        self,
        character_id: uuid.UUID,
        timeline_id: uuid.UUID,
    ) -> CharacterStateHistory | None:
        return self._db.scalar(
            select(CharacterStateHistory)
            .where(
                CharacterStateHistory.character_id == character_id,
                CharacterStateHistory.timeline_id == timeline_id,
            )
            .order_by(CharacterStateHistory.created_at.desc())
            .limit(1)
        )

    def _character_memories(
        self,
        character_id: uuid.UUID,
        timeline_id: uuid.UUID,
        *,
        memory_types: set[str] | None = None,
        excluded_types: set[str] | None = None,
        limit: int,
    ) -> list[str]:
        query = select(MemoryEntry).where(
            MemoryEntry.entity_type == "character",
            MemoryEntry.entity_id == character_id,
            MemoryEntry.timeline_id == timeline_id,
        )
        if memory_types:
            query = query.where(MemoryEntry.memory_type.in_(memory_types))
        if excluded_types:
            query = query.where(MemoryEntry.memory_type.not_in(excluded_types))

        return [
            entry.content
            for entry in self._db.scalars(
                query.order_by(MemoryEntry.created_at.desc()).limit(limit)
            ).all()
        ]

    def _string_items(self, payload: dict[str, Any], key: str) -> list[str]:
        value = payload.get(key)
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []
