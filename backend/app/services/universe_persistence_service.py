from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.character import Character
from app.db.models.character_state_history import CharacterStateHistory
from app.db.models.event import Event
from app.db.models.event_participant import EventParticipant
from app.db.models.location import Location
from app.db.models.memory_entry import MemoryEntry
from app.db.models.relationship import Relationship as CharacterRelationship
from app.db.models.source_input import SourceInput
from app.db.models.timeline import Timeline
from app.db.models.timeline_commit import TimelineCommit
from app.db.models.timeline_commit_event import TimelineCommitEvent
from app.db.models.universe import Universe
from app.db.models.world_object import WorldObject
from app.schemas.extraction import UniverseExtraction
from app.schemas.source import SourcePayload


@dataclass(slots=True)
class PersistenceResult:
    universe: Universe
    source_input: SourceInput
    timeline: Timeline
    commit: TimelineCommit
    characters: list[Character]
    locations: list[Location]
    objects: list[WorldObject]
    events: list[Event]
    relationships: list[CharacterRelationship]


class UniversePersistenceService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def persist_extraction(
        self,
        *,
        extraction: UniverseExtraction,
        source: SourcePayload,
        universe_id: uuid.UUID | None = None,
    ) -> PersistenceResult:
        universe = self._upsert_universe(extraction, universe_id)
        self._db.flush()

        source_input = SourceInput(
            universe_id=universe.id,
            input_type=source.source_type,
            title=source.title_hint or extraction.universe.title,
            raw_text=source.content,
            status="processed",
        )
        self._db.add(source_input)

        timeline = self._ensure_canon_timeline(universe)
        self._db.flush()

        commit = TimelineCommit(
            timeline_id=timeline.id,
            parent_commit_id=timeline.head_commit_id,
            message="Initial universe extraction",
            commit_type="ingest",
            created_by="world_architect",
        )
        self._db.add(commit)
        self._db.flush()

        characters = self._create_characters(universe.id, extraction)
        locations = self._create_locations(universe.id, extraction)
        objects = self._create_objects(universe.id, extraction)
        self._db.flush()
        self._create_initial_character_memory(
            characters=characters,
            universe_id=universe.id,
            timeline_id=timeline.id,
            commit_id=commit.id,
        )

        character_by_name = {
            self._normalize(character.canonical_name): character for character in characters
        }
        location_by_name = {self._normalize(location.name): location for location in locations}

        events = self._create_events(
            universe_id=universe.id,
            timeline_id=timeline.id,
            commit_id=commit.id,
            extraction=extraction,
            character_by_name=character_by_name,
            location_by_name=location_by_name,
        )
        self._db.flush()

        relationships = self._create_relationships(
            universe_id=universe.id,
            timeline_id=timeline.id,
            extraction=extraction,
            character_by_name=character_by_name,
        )
        self._create_world_rule_memory(
            universe_id=universe.id,
            timeline_id=timeline.id,
            commit_id=commit.id,
            extraction=extraction,
        )

        timeline.head_commit_id = commit.id
        universe.active_timeline_id = timeline.id
        universe.status = "ready"

        self._db.add(universe)
        self._db.add(timeline)
        self._db.commit()

        persisted_entities = [
            universe,
            source_input,
            timeline,
            commit,
            *characters,
            *locations,
            *objects,
            *events,
            *relationships,
        ]
        for entity in persisted_entities:
            self._db.refresh(entity)

        return PersistenceResult(
            universe=universe,
            source_input=source_input,
            timeline=timeline,
            commit=commit,
            characters=characters,
            locations=locations,
            objects=objects,
            events=events,
            relationships=relationships,
        )

    def _upsert_universe(
        self,
        extraction: UniverseExtraction,
        universe_id: uuid.UUID | None,
    ) -> Universe:
        extracted = extraction.universe
        if universe_id is None:
            universe = Universe(
                title=extracted.title,
                tagline="Create worlds, not clips.",
                premise=extracted.premise,
                genre=extracted.genre,
                tone=extracted.tone,
                status="extracting",
            )
            self._db.add(universe)
            return universe

        universe = self._db.get(Universe, universe_id)
        if universe is None:
            raise NotFoundError("Universe", universe_id)

        universe.title = extracted.title
        universe.premise = extracted.premise
        universe.genre = extracted.genre
        universe.tone = extracted.tone
        universe.status = "extracting"
        self._db.add(universe)
        return universe

    def _ensure_canon_timeline(self, universe: Universe) -> Timeline:
        if universe.active_timeline_id:
            timeline = self._db.get(Timeline, universe.active_timeline_id)
            if timeline is not None:
                return timeline

        timeline = Timeline(universe_id=universe.id, name="Main Timeline", is_canon=True)
        self._db.add(timeline)
        return timeline

    def _create_characters(
        self,
        universe_id: uuid.UUID,
        extraction: UniverseExtraction,
    ) -> list[Character]:
        characters: list[Character] = []
        seen: set[str] = set()
        for extracted in extraction.characters:
            normalized = self._normalize(extracted.name)
            if normalized in seen:
                continue
            seen.add(normalized)
            character = Character(
                universe_id=universe_id,
                canonical_name=extracted.name,
                aliases=[],
                description=extracted.description,
                traits={"personality": extracted.personality},
                goals={"items": extracted.goals},
                fears={"items": extracted.fears},
                status=extracted.current_status,
            )
            self._db.add(character)
            characters.append(character)
        return characters

    def _create_locations(
        self,
        universe_id: uuid.UUID,
        extraction: UniverseExtraction,
    ) -> list[Location]:
        locations: list[Location] = []
        seen: set[str] = set()
        for extracted in extraction.locations:
            normalized = self._normalize(extracted.name)
            if normalized in seen:
                continue
            seen.add(normalized)
            location = Location(
                universe_id=universe_id,
                name=extracted.name,
                description=extracted.description,
                location_type=extracted.type,
                rules={},
            )
            self._db.add(location)
            locations.append(location)
        return locations

    def _create_objects(
        self,
        universe_id: uuid.UUID,
        extraction: UniverseExtraction,
    ) -> list[WorldObject]:
        objects: list[WorldObject] = []
        seen: set[str] = set()
        for extracted in extraction.objects:
            normalized = self._normalize(extracted.name)
            if normalized in seen:
                continue
            seen.add(normalized)
            description = f"{extracted.description}\n\nImportance: {extracted.importance}"
            world_object = WorldObject(
                universe_id=universe_id,
                name=extracted.name,
                description=description,
                object_type="story_object",
                status="active",
            )
            self._db.add(world_object)
            objects.append(world_object)
        return objects

    def _create_events(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        extraction: UniverseExtraction,
        character_by_name: dict[str, Character],
        location_by_name: dict[str, Location],
    ) -> list[Event]:
        events: list[Event] = []
        for index, extracted in enumerate(extraction.events, start=1):
            location = (
                location_by_name.get(self._normalize(extracted.location))
                if extracted.location
                else None
            )
            event = Event(
                universe_id=universe_id,
                location_id=location.id if location else None,
                title=extracted.title,
                summary=extracted.summary,
                event_type="extracted_story_event",
                order_index=index,
                importance=extracted.importance,
            )
            self._db.add(event)
            self._db.flush()

            self._db.add(
                TimelineCommitEvent(commit_id=commit_id, event_id=event.id, change_type="created")
            )

            for participant_name in extracted.participants:
                character = character_by_name.get(self._normalize(participant_name))
                if character is None:
                    continue
                self._db.add(
                    EventParticipant(
                        event_id=event.id,
                        character_id=character.id,
                        role="participant",
                    )
                )
                self._create_event_character_memories(
                    character=character,
                    event=event,
                    location_name=location.name if location else None,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                )

            events.append(event)
        return events

    def _create_relationships(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        extraction: UniverseExtraction,
        character_by_name: dict[str, Character],
    ) -> list[CharacterRelationship]:
        relationships: list[CharacterRelationship] = []
        seen: set[tuple[uuid.UUID, uuid.UUID, str]] = set()
        for extracted in extraction.relationships:
            source = character_by_name.get(self._normalize(extracted.source_character))
            target = character_by_name.get(self._normalize(extracted.target_character))
            if source is None or target is None or source.id == target.id:
                continue

            key = (source.id, target.id, extracted.type)
            if key in seen:
                continue
            seen.add(key)

            relationship = CharacterRelationship(
                universe_id=universe_id,
                timeline_id=timeline_id,
                source_character_id=source.id,
                target_character_id=target.id,
                relationship_type=extracted.type,
                strength=extracted.strength,
                status="active",
                evidence="Extracted from source input by World Architect.",
                confidence=0.85,
            )
            self._db.add(relationship)
            relationships.append(relationship)
        return relationships

    def _create_world_rule_memory(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        extraction: UniverseExtraction,
    ) -> None:
        for rule in extraction.universe.world_rules:
            normalized_rule = rule.strip()
            if not normalized_rule:
                continue
            self._db.add(
                MemoryEntry(
                    universe_id=universe_id,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    entity_type="universe",
                    entity_id=universe_id,
                    memory_type="world_rule",
                    content=normalized_rule,
                    structured_value={"rule": normalized_rule},
                    confidence=0.95,
                    source="world_extraction",
                )
            )

    def _create_initial_character_memory(
        self,
        *,
        characters: list[Character],
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
    ) -> None:
        for character in characters:
            self._db.add(
                CharacterStateHistory(
                    universe_id=universe_id,
                    character_id=character.id,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    current_status=character.status,
                    emotional_state="unknown",
                    physical_state=character.status,
                    summary=(
                        f"{character.canonical_name} enters the universe "
                        f"as {character.status}."
                    ),
                    source="world_extraction",
                    confidence=0.85,
                )
            )
            if character.description:
                self._add_character_memory(
                    character=character,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    memory_type="character_memory",
                    content=character.description,
                    structured_value={"kind": "profile"},
                )
            for trait in character.traits.get("personality", []):
                self._add_character_memory(
                    character=character,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    memory_type="personality",
                    content=f"Personality trait: {trait}",
                    structured_value={"trait": trait},
                )
            for goal in character.goals.get("items", []):
                self._add_character_memory(
                    character=character,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    memory_type="goal",
                    content=f"Goal: {goal}",
                    structured_value={"goal": goal},
                )
            for fear in character.fears.get("items", []):
                self._add_character_memory(
                    character=character,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    memory_type="fear",
                    content=f"Fear: {fear}",
                    structured_value={"fear": fear},
                )

    def _create_event_character_memories(
        self,
        *,
        character: Character,
        event: Event,
        location_name: str | None,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
    ) -> None:
        event_payload = {
            "event_id": str(event.id),
            "event_title": event.title,
            "importance": event.importance,
            "order_index": event.order_index,
            "location_name": location_name,
        }
        self._add_character_memory(
            character=character,
            timeline_id=timeline_id,
            commit_id=commit_id,
            memory_type="knowledge",
            content=f"Knows about {event.title}: {event.summary or 'No summary recorded.'}",
            structured_value=event_payload,
            valid_from_event_id=event.id,
        )
        self._add_character_memory(
            character=character,
            timeline_id=timeline_id,
            commit_id=commit_id,
            memory_type="character_arc_event",
            content=f"{character.canonical_name} was part of {event.title}. {event.summary or ''}",
            structured_value=event_payload,
            valid_from_event_id=event.id,
        )

    def _add_character_memory(
        self,
        *,
        character: Character,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        memory_type: str,
        content: str,
        structured_value: dict[str, object],
        valid_from_event_id: uuid.UUID | None = None,
    ) -> None:
        if not content.strip():
            return
        self._db.add(
            MemoryEntry(
                universe_id=character.universe_id,
                timeline_id=timeline_id,
                commit_id=commit_id,
                entity_type="character",
                entity_id=character.id,
                memory_type=memory_type,
                content=content.strip(),
                structured_value=structured_value,
                confidence=0.85,
                source="world_extraction",
                valid_from_event_id=valid_from_event_id,
            )
        )

    def _normalize(self, value: str | None) -> str:
        return " ".join((value or "").casefold().split())
