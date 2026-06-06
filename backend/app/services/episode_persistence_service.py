from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.character import Character
from app.db.models.character_state_history import CharacterStateHistory
from app.db.models.episode import Episode
from app.db.models.event import Event
from app.db.models.event_participant import EventParticipant
from app.db.models.location import Location
from app.db.models.memory_entry import MemoryEntry
from app.db.models.relationship import Relationship
from app.db.models.scene import Scene
from app.db.models.scene_participant import SceneParticipant
from app.db.models.timeline import Timeline
from app.db.models.timeline_commit import TimelineCommit
from app.db.models.timeline_commit_event import TimelineCommitEvent
from app.db.models.universe import Universe
from app.schemas.episode_generation import (
    EpisodeContextPack,
    EpisodeOutline,
    GeneratedEpisode,
    GeneratedEventMemory,
    GeneratedScene,
)


@dataclass(slots=True)
class EpisodePersistenceResult:
    episode: Episode
    scenes: list[Scene]
    events: list[Event]
    memory_entries: list[MemoryEntry]


class EpisodePersistenceService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def persist_episode(
        self,
        *,
        context: EpisodeContextPack,
        outline: EpisodeOutline,
        generated: GeneratedEpisode,
    ) -> EpisodePersistenceResult:
        universe_id = uuid.UUID(context.universe.id)
        timeline_id = uuid.UUID(context.timeline_id)
        universe = self._db.get(Universe, universe_id)
        timeline = self._db.get(Timeline, timeline_id)
        if universe is None:
            raise NotFoundError("Universe", universe_id)
        if timeline is None:
            raise NotFoundError("Timeline", timeline_id)

        commit = TimelineCommit(
            timeline_id=timeline.id,
            parent_commit_id=timeline.head_commit_id,
            message=f"Generated episode: {generated.title}",
            commit_type="episode_generation",
            created_by="director_agent",
        )
        self._db.add(commit)
        self._db.flush()

        episode = Episode(
            universe_id=universe.id,
            timeline_id=timeline.id,
            commit_id=commit.id,
            title=generated.title,
            logline=outline.logline,
            summary=generated.summary,
            status="generated",
        )
        self._db.add(episode)
        self._db.flush()

        character_by_name = self._characters_by_name(universe.id)
        location_by_name = self._locations_by_name(universe.id)
        scenes: list[Scene] = []
        events: list[Event] = []
        memory_entries: list[MemoryEntry] = []
        next_event_order = self._next_event_order(universe.id)

        memory_entries.append(
            self._add_memory_entry(
                universe_id=universe.id,
                timeline_id=timeline.id,
                commit_id=commit.id,
                entity_type="universe",
                entity_id=universe.id,
                memory_type="episode_summary",
                content=f"{episode.title}: {episode.summary or generated.summary}",
                structured_value={
                    "episode_id": str(episode.id),
                    "episode_title": episode.title,
                },
                source="episode_generation",
            )
        )

        for generated_scene in sorted(generated.scenes, key=lambda scene: scene.scene_number):
            location = self._resolve_location(
                universe_id=universe.id,
                location_name=generated_scene.location,
                location_by_name=location_by_name,
                episode_title=episode.title,
            )
            scene = self._create_scene(
                episode=episode,
                generated_scene=generated_scene,
                location=location,
                character_by_name=character_by_name,
            )
            scenes.append(scene)

            event = self._create_scene_event(
                universe_id=universe.id,
                timeline_id=timeline.id,
                commit_id=commit.id,
                scene=scene,
                generated_scene=generated_scene,
                location=location,
                character_by_name=character_by_name,
                order_index=next_event_order,
            )
            next_event_order += 1
            events.append(event)

            memory_entries.extend(
                self._create_scene_memories(
                    universe_id=universe.id,
                    timeline_id=timeline.id,
                    commit_id=commit.id,
                    episode=episode,
                    scene=scene,
                    generated_scene=generated_scene,
                    event=event,
                    character_by_name=character_by_name,
                )
            )

        for event_memory in generated.new_event_memories:
            event = self._create_generated_event_memory(
                universe_id=universe.id,
                timeline_id=timeline.id,
                commit_id=commit.id,
                event_memory=event_memory,
                location_by_name=location_by_name,
                character_by_name=character_by_name,
                order_index=next_event_order,
            )
            next_event_order += 1
            events.append(event)
            memory_entries.append(
                self._add_memory_entry(
                    universe_id=universe.id,
                    timeline_id=timeline.id,
                    commit_id=commit.id,
                    entity_type="universe",
                    entity_id=universe.id,
                    memory_type="generated_event",
                    content=f"{event.title}: {event.summary or event_memory.summary}",
                    structured_value={
                        "event_id": str(event.id),
                        "importance": event.importance,
                    },
                    source="episode_generation",
                    valid_from_event_id=event.id,
                )
            )

        memory_entries.extend(
            self._apply_relationship_changes(
                universe_id=universe.id,
                timeline_id=timeline.id,
                commit_id=commit.id,
                generated=generated,
                character_by_name=character_by_name,
            )
        )
        memory_entries.extend(
            self._apply_character_state_changes(
                universe_id=universe.id,
                timeline_id=timeline.id,
                commit_id=commit.id,
                generated=generated,
                character_by_name=character_by_name,
            )
        )
        memory_entries.extend(
            self._apply_knowledge_changes(
                universe_id=universe.id,
                timeline_id=timeline.id,
                commit_id=commit.id,
                generated=generated,
                character_by_name=character_by_name,
            )
        )

        timeline.head_commit_id = commit.id
        universe.active_timeline_id = timeline.id
        self._db.add(timeline)
        self._db.add(universe)
        self._db.commit()

        self._db.refresh(episode)
        for scene in scenes:
            self._db.refresh(scene)
        return EpisodePersistenceResult(
            episode=episode,
            scenes=scenes,
            events=events,
            memory_entries=memory_entries,
        )

    def _create_scene(
        self,
        *,
        episode: Episode,
        generated_scene: GeneratedScene,
        location: Location | None,
        character_by_name: dict[str, Character],
    ) -> Scene:
        scene = Scene(
            episode_id=episode.id,
            location_id=location.id if location else None,
            scene_number=generated_scene.scene_number,
            title=generated_scene.title,
            summary=generated_scene.outcome,
            dialogue=self._format_dialogue(generated_scene),
            visual_direction=generated_scene.description,
        )
        self._db.add(scene)
        self._db.flush()

        seen_participants: set[uuid.UUID] = set()
        for character_name in generated_scene.characters:
            character = character_by_name.get(self._normalize(character_name))
            if character is None or character.id in seen_participants:
                continue
            seen_participants.add(character.id)
            self._db.add(
                SceneParticipant(
                    scene_id=scene.id,
                    character_id=character.id,
                    role="primary",
                )
            )
        return scene

    def _create_scene_event(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        scene: Scene,
        generated_scene: GeneratedScene,
        location: Location | None,
        character_by_name: dict[str, Character],
        order_index: int,
    ) -> Event:
        event = Event(
            universe_id=universe_id,
            location_id=location.id if location else None,
            title=generated_scene.title,
            summary=generated_scene.outcome,
            event_type="generated_episode_scene",
            order_index=order_index,
            importance=7,
        )
        self._db.add(event)
        self._db.flush()
        self._db.add(
            TimelineCommitEvent(
                commit_id=commit_id,
                event_id=event.id,
                change_type="created",
            )
        )

        seen_participants: set[uuid.UUID] = set()
        for character_name in generated_scene.characters:
            character = character_by_name.get(self._normalize(character_name))
            if character is None or character.id in seen_participants:
                continue
            seen_participants.add(character.id)
            self._db.add(
                EventParticipant(
                    event_id=event.id,
                    character_id=character.id,
                    role="participant",
                )
            )
        return event

    def _create_scene_memories(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        episode: Episode,
        scene: Scene,
        generated_scene: GeneratedScene,
        event: Event,
        character_by_name: dict[str, Character],
    ) -> list[MemoryEntry]:
        entries: list[MemoryEntry] = [
            self._add_memory_entry(
                universe_id=universe_id,
                timeline_id=timeline_id,
                commit_id=commit_id,
                entity_type="episode",
                entity_id=episode.id,
                memory_type="scene_outcome",
                content=f"Scene {generated_scene.scene_number} outcome: {generated_scene.outcome}",
                structured_value={
                    "episode_id": str(episode.id),
                    "scene_id": str(scene.id),
                    "scene_number": generated_scene.scene_number,
                    "event_id": str(event.id),
                },
                source="episode_generation",
                valid_from_event_id=event.id,
            )
        ]

        for implication in generated_scene.memory_implications:
            entries.append(
                self._add_memory_entry(
                    universe_id=universe_id,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    entity_type="episode",
                    entity_id=episode.id,
                    memory_type="memory_implication",
                    content=implication,
                    structured_value={
                        "episode_id": str(episode.id),
                        "scene_id": str(scene.id),
                        "scene_number": generated_scene.scene_number,
                    },
                    source="episode_generation",
                    valid_from_event_id=event.id,
                )
            )

        for character_name in generated_scene.characters:
            character = character_by_name.get(self._normalize(character_name))
            if character is None:
                continue
            entries.append(
                self._add_memory_entry(
                    universe_id=universe_id,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    entity_type="character",
                    entity_id=character.id,
                    memory_type="character_arc_event",
                    content=(
                        f"{character.canonical_name} participated in "
                        f"{generated_scene.title}: {generated_scene.outcome}"
                    ),
                    structured_value={
                        "episode_id": str(episode.id),
                        "scene_id": str(scene.id),
                        "scene_number": generated_scene.scene_number,
                        "event_id": str(event.id),
                    },
                    source="episode_generation",
                    valid_from_event_id=event.id,
                )
            )
        return entries

    def _create_generated_event_memory(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        event_memory: GeneratedEventMemory,
        location_by_name: dict[str, Location],
        character_by_name: dict[str, Character],
        order_index: int,
    ) -> Event:
        location = (
            location_by_name.get(self._normalize(event_memory.location))
            if event_memory.location
            else None
        )
        event = Event(
            universe_id=universe_id,
            location_id=location.id if location else None,
            title=event_memory.title,
            summary=event_memory.summary,
            event_type="episode_memory_update",
            order_index=order_index,
            importance=event_memory.importance,
        )
        self._db.add(event)
        self._db.flush()
        self._db.add(
            TimelineCommitEvent(
                commit_id=commit_id,
                event_id=event.id,
                change_type="created",
            )
        )

        seen_participants: set[uuid.UUID] = set()
        for character_name in event_memory.participants:
            character = character_by_name.get(self._normalize(character_name))
            if character is None or character.id in seen_participants:
                continue
            seen_participants.add(character.id)
            self._db.add(
                EventParticipant(
                    event_id=event.id,
                    character_id=character.id,
                    role="participant",
                )
            )
        return event

    def _apply_relationship_changes(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        generated: GeneratedEpisode,
        character_by_name: dict[str, Character],
    ) -> list[MemoryEntry]:
        entries: list[MemoryEntry] = []
        for change in generated.relationship_changes:
            source = character_by_name.get(self._normalize(change.source_character))
            target = character_by_name.get(self._normalize(change.target_character))
            if source is None or target is None or source.id == target.id:
                continue

            relationship = self._db.scalar(
                select(Relationship)
                .where(
                    Relationship.universe_id == universe_id,
                    Relationship.timeline_id == timeline_id,
                    Relationship.source_character_id == source.id,
                    Relationship.target_character_id == target.id,
                    Relationship.relationship_type == change.relationship_type,
                    Relationship.status == "active",
                )
                .limit(1)
            )
            if relationship is None:
                relationship = Relationship(
                    universe_id=universe_id,
                    timeline_id=timeline_id,
                    source_character_id=source.id,
                    target_character_id=target.id,
                    relationship_type=change.relationship_type,
                    strength=self._clamp_strength(change.strength_delta),
                    status="active",
                    evidence=change.rationale,
                    confidence=0.8,
                )
            else:
                current_strength = relationship.strength or 0
                relationship.strength = self._clamp_strength(
                    current_strength + change.strength_delta
                )
                relationship.evidence = change.rationale
                relationship.confidence = max(relationship.confidence or 0, 0.8)
            self._db.add(relationship)
            self._db.flush()

            content = (
                f"{source.canonical_name} -> {target.canonical_name} "
                f"{change.relationship_type} changed by {change.strength_delta}: "
                f"{change.rationale}"
            )
            entries.append(
                self._add_memory_entry(
                    universe_id=universe_id,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    entity_type="relationship",
                    entity_id=relationship.id,
                    memory_type="relationship_change",
                    content=content,
                    structured_value={
                        "source_character_id": str(source.id),
                        "target_character_id": str(target.id),
                        "relationship_type": change.relationship_type,
                        "strength_delta": change.strength_delta,
                    },
                    source="episode_generation",
                )
            )
        return entries

    def _apply_character_state_changes(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        generated: GeneratedEpisode,
        character_by_name: dict[str, Character],
    ) -> list[MemoryEntry]:
        entries: list[MemoryEntry] = []
        for change in generated.character_state_changes:
            character = character_by_name.get(self._normalize(change.character))
            if character is None:
                continue

            character.status = change.current_status
            self._db.add(character)
            self._db.add(
                CharacterStateHistory(
                    universe_id=universe_id,
                    character_id=character.id,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    current_status=change.current_status,
                    emotional_state=change.emotional_state,
                    physical_state=change.physical_state,
                    summary=change.summary,
                    source="episode_generation",
                    confidence=0.82,
                )
            )
            entries.append(
                self._add_memory_entry(
                    universe_id=universe_id,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    entity_type="character",
                    entity_id=character.id,
                    memory_type="state_change",
                    content=change.summary,
                    structured_value={
                        "current_status": change.current_status,
                        "emotional_state": change.emotional_state,
                        "physical_state": change.physical_state,
                    },
                    source="episode_generation",
                )
            )
        return entries

    def _apply_knowledge_changes(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        generated: GeneratedEpisode,
        character_by_name: dict[str, Character],
    ) -> list[MemoryEntry]:
        entries: list[MemoryEntry] = []
        for change in generated.knowledge_changes:
            character = character_by_name.get(self._normalize(change.character))
            if character is None:
                continue
            entries.append(
                self._add_memory_entry(
                    universe_id=universe_id,
                    timeline_id=timeline_id,
                    commit_id=commit_id,
                    entity_type="character",
                    entity_id=character.id,
                    memory_type="knowledge",
                    content=change.knowledge,
                    structured_value={
                        "secrecy_level": change.secrecy_level,
                        "source_scene_number": change.source_scene_number,
                    },
                    source="episode_generation",
                )
            )
        return entries

    def _add_memory_entry(
        self,
        *,
        universe_id: uuid.UUID,
        timeline_id: uuid.UUID,
        commit_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID | None,
        memory_type: str,
        content: str,
        structured_value: dict[str, object],
        source: str,
        valid_from_event_id: uuid.UUID | None = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            universe_id=universe_id,
            timeline_id=timeline_id,
            commit_id=commit_id,
            entity_type=entity_type,
            entity_id=entity_id,
            memory_type=memory_type,
            content=content.strip(),
            structured_value=structured_value,
            confidence=0.82,
            source=source,
            valid_from_event_id=valid_from_event_id,
        )
        self._db.add(entry)
        self._db.flush()
        return entry

    def _resolve_location(
        self,
        *,
        universe_id: uuid.UUID,
        location_name: str,
        location_by_name: dict[str, Location],
        episode_title: str,
    ) -> Location | None:
        normalized = self._normalize(location_name)
        if not normalized:
            return None

        location = location_by_name.get(normalized)
        if location is not None:
            return location

        location = Location(
            universe_id=universe_id,
            name=location_name.strip(),
            description=f"Introduced during generated episode '{episode_title}'.",
            location_type="generated_location",
            rules={},
        )
        self._db.add(location)
        self._db.flush()
        location_by_name[normalized] = location
        return location

    def _characters_by_name(self, universe_id: uuid.UUID) -> dict[str, Character]:
        characters = self._db.scalars(
            select(Character).where(Character.universe_id == universe_id)
        ).all()
        return {self._normalize(character.canonical_name): character for character in characters}

    def _locations_by_name(self, universe_id: uuid.UUID) -> dict[str, Location]:
        locations = self._db.scalars(
            select(Location).where(Location.universe_id == universe_id)
        ).all()
        return {self._normalize(location.name): location for location in locations}

    def _next_event_order(self, universe_id: uuid.UUID) -> int:
        max_order = self._db.scalar(
            select(func.max(Event.order_index)).where(Event.universe_id == universe_id)
        )
        return int(max_order or 0) + 1

    def _format_dialogue(self, scene: GeneratedScene) -> str:
        return "\n".join(
            f"{line.character.upper()}: {line.line}" for line in scene.dialogue
        )

    def _normalize(self, value: str | None) -> str:
        return " ".join((value or "").casefold().split())

    def _clamp_strength(self, value: int) -> int:
        return max(-100, min(100, value))
