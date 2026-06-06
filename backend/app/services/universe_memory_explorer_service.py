from __future__ import annotations

import uuid
from typing import Any

from neo4j.exceptions import Neo4jError
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.db.models.character import Character
from app.db.models.event import Event
from app.db.models.event_participant import EventParticipant
from app.db.models.location import Location
from app.db.models.memory_entry import MemoryEntry
from app.db.models.relationship import Relationship
from app.db.models.timeline import Timeline
from app.db.models.universe import Universe
from app.db.models.world_object import WorldObject
from app.schemas.memory_explorer import (
    MemoryEventRead,
    MemoryGraphEdge,
    MemoryGraphNode,
    MemoryLocationRead,
    MemoryObjectRead,
    MemoryParticipant,
    MemoryRelationshipRead,
    UniverseGraphResponse,
    UniverseMemoryOverview,
    UniverseMemoryStats,
)
from app.services.neo4j_graph_aggregation_service import Neo4jGraphAggregationService


class UniverseMemoryExplorerService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def overview(self, universe_id: uuid.UUID) -> UniverseMemoryOverview:
        self._ensure_universe(universe_id)
        return UniverseMemoryOverview(
            universe_id=universe_id,
            stats=UniverseMemoryStats(
                characters=self._count(Character, universe_id),
                locations=self._count(Location, universe_id),
                events=self._count(Event, universe_id),
                objects=self._count(WorldObject, universe_id),
                relationships=self._count(Relationship, universe_id),
                memory_entries=self._count(MemoryEntry, universe_id),
                timelines=self._count(Timeline, universe_id),
            ),
        )

    def graph(self, universe_id: uuid.UUID) -> UniverseGraphResponse:
        self._ensure_universe(universe_id)
        warnings: list[str] = []
        try:
            neo4j_graph = Neo4jGraphAggregationService().get_graph(universe_id)
        except (Neo4jError, OSError, RuntimeError) as error:
            warnings.append(f"Neo4j graph unavailable: {error}")
            neo4j_graph = UniverseGraphResponse(
                universe_id=universe_id,
                source="postgres_fallback",
                nodes=[],
                edges=[],
            )

        fallback = self._postgres_graph(universe_id)
        if not neo4j_graph.nodes:
            fallback.warnings = warnings
            return fallback

        merged = self._merge_graphs(primary=neo4j_graph, fallback=fallback)
        merged.source = "neo4j"
        merged.warnings = warnings
        return merged

    def events(self, universe_id: uuid.UUID) -> list[MemoryEventRead]:
        self._ensure_universe(universe_id)
        statement = (
            select(Event)
            .where(Event.universe_id == universe_id)
            .options(
                joinedload(Event.location),
                joinedload(Event.participants).joinedload(EventParticipant.character),
            )
            .order_by(Event.order_index.asc().nullslast(), Event.created_at.asc())
        )
        return [self._event_read(event) for event in self._db.scalars(statement).unique()]

    def relationships(self, universe_id: uuid.UUID) -> list[MemoryRelationshipRead]:
        self._ensure_universe(universe_id)
        statement = (
            select(Relationship)
            .where(Relationship.universe_id == universe_id)
            .options(
                joinedload(Relationship.source_character),
                joinedload(Relationship.target_character),
            )
            .order_by(Relationship.relationship_type.asc(), Relationship.created_at.asc())
        )
        return [
            self._relationship_read(relationship)
            for relationship in self._db.scalars(statement).unique()
        ]

    def locations(self, universe_id: uuid.UUID) -> list[MemoryLocationRead]:
        self._ensure_universe(universe_id)
        statement = (
            select(Location)
            .where(Location.universe_id == universe_id)
            .order_by(Location.name.asc())
        )
        return [
            MemoryLocationRead(
                id=location.id,
                name=location.name,
                description=location.description,
                location_type=location.location_type,
            )
            for location in self._db.scalars(statement)
        ]

    def objects(self, universe_id: uuid.UUID) -> list[MemoryObjectRead]:
        self._ensure_universe(universe_id)
        statement = (
            select(WorldObject)
            .where(WorldObject.universe_id == universe_id)
            .order_by(WorldObject.name.asc())
        )
        return [
            MemoryObjectRead(
                id=world_object.id,
                name=world_object.name,
                description=world_object.description,
                object_type=world_object.object_type,
                status=world_object.status,
                current_owner_character_id=world_object.current_owner_character_id,
                current_location_id=world_object.current_location_id,
            )
            for world_object in self._db.scalars(statement)
        ]

    def _postgres_graph(self, universe_id: uuid.UUID) -> UniverseGraphResponse:
        nodes: dict[str, MemoryGraphNode] = {}
        edges: dict[str, MemoryGraphEdge] = {}
        relationship_counts = self._relationship_counts(universe_id)

        for character in self._characters(universe_id):
            nodes[str(character.id)] = MemoryGraphNode(
                id=str(character.id),
                type="character",
                label=character.canonical_name,
                subtitle=character.status,
                properties={
                    "status": character.status,
                    "description": character.description,
                    "relationship_count": relationship_counts.get(character.id, 0),
                },
            )

        for event in self._events_raw(universe_id):
            participants = [
                participant.character.canonical_name for participant in event.participants
            ]
            nodes[str(event.id)] = MemoryGraphNode(
                id=str(event.id),
                type="event",
                label=event.title,
                subtitle=f"importance {event.importance}" if event.importance else None,
                properties={
                    "summary": event.summary,
                    "importance": event.importance,
                    "order_index": event.order_index,
                    "participants": participants,
                    "participant_count": len(participants),
                },
            )
            for participant in event.participants:
                edge_id = f"{participant.character_id}:{event.id}:PARTICIPATED_IN"
                edges[edge_id] = MemoryGraphEdge(
                    id=edge_id,
                    source=str(participant.character_id),
                    target=str(event.id),
                    type="PARTICIPATED_IN",
                    label="Participated In",
                    properties={"role": participant.role},
                )
            if event.location_id:
                edge_id = f"{event.id}:{event.location_id}:OCCURRED_AT"
                edges[edge_id] = MemoryGraphEdge(
                    id=edge_id,
                    source=str(event.id),
                    target=str(event.location_id),
                    type="OCCURRED_AT",
                    label="Occurred At",
                    properties={},
                )

        for location in self.locations(universe_id):
            nodes[str(location.id)] = MemoryGraphNode(
                id=str(location.id),
                type="location",
                label=location.name,
                subtitle=location.location_type,
                properties={
                    "description": location.description,
                    "location_type": location.location_type,
                },
            )

        for world_object in self.objects(universe_id):
            nodes[str(world_object.id)] = MemoryGraphNode(
                id=str(world_object.id),
                type="object",
                label=world_object.name,
                subtitle=world_object.object_type,
                properties={
                    "description": world_object.description,
                    "object_type": world_object.object_type,
                    "status": world_object.status,
                },
            )
            if world_object.current_owner_character_id:
                edge_id = f"{world_object.current_owner_character_id}:{world_object.id}:OWNS"
                edges[edge_id] = MemoryGraphEdge(
                    id=edge_id,
                    source=str(world_object.current_owner_character_id),
                    target=str(world_object.id),
                    type="OWNS",
                    label="Owns",
                    properties={},
                )

        for relationship in self.relationships(universe_id):
            edge_id = (
                f"{relationship.source_character_id}:"
                f"{relationship.target_character_id}:"
                f"{relationship.relationship_type}"
            )
            edges[edge_id] = MemoryGraphEdge(
                id=edge_id,
                source=str(relationship.source_character_id),
                target=str(relationship.target_character_id),
                type=relationship.relationship_type,
                label=relationship.relationship_type.replace("_", " ").title(),
                strength=relationship.strength,
                properties={"status": relationship.status, "evidence": relationship.evidence},
            )

        return UniverseGraphResponse(
            universe_id=universe_id,
            source="postgres_fallback",
            nodes=list(nodes.values()),
            edges=list(edges.values()),
        )

    def _merge_graphs(
        self,
        *,
        primary: UniverseGraphResponse,
        fallback: UniverseGraphResponse,
    ) -> UniverseGraphResponse:
        nodes = {node.id: node for node in fallback.nodes}
        for node in primary.nodes:
            fallback_node = nodes.get(node.id)
            if fallback_node:
                node.properties = {**fallback_node.properties, **node.properties}
                if node.subtitle is None:
                    node.subtitle = fallback_node.subtitle
            nodes[node.id] = node

        edges = {edge.id: edge for edge in fallback.edges}
        for edge in primary.edges:
            edge_id = f"{edge.source}:{edge.target}:{edge.type}"
            edges[edge_id] = edge.model_copy(update={"id": edge_id})

        return UniverseGraphResponse(
            universe_id=primary.universe_id,
            source=primary.source,
            nodes=list(nodes.values()),
            edges=list(edges.values()),
        )

    def _characters(self, universe_id: uuid.UUID) -> list[Character]:
        statement = (
            select(Character)
            .where(Character.universe_id == universe_id)
            .order_by(Character.canonical_name.asc())
        )
        return list(self._db.scalars(statement))

    def _events_raw(self, universe_id: uuid.UUID) -> list[Event]:
        statement = (
            select(Event)
            .where(Event.universe_id == universe_id)
            .options(joinedload(Event.participants).joinedload(EventParticipant.character))
            .order_by(Event.order_index.asc().nullslast(), Event.created_at.asc())
        )
        return list(self._db.scalars(statement).unique())

    def _event_read(self, event: Event) -> MemoryEventRead:
        return MemoryEventRead(
            id=event.id,
            title=event.title,
            summary=event.summary,
            importance=event.importance,
            order_index=event.order_index,
            location_id=event.location_id,
            location_name=event.location.name if event.location else None,
            participants=[
                MemoryParticipant(
                    id=participant.character_id,
                    name=participant.character.canonical_name,
                )
                for participant in event.participants
            ],
        )

    def _relationship_read(self, relationship: Relationship) -> MemoryRelationshipRead:
        return MemoryRelationshipRead(
            id=relationship.id,
            source_character_id=relationship.source_character_id,
            source_character_name=relationship.source_character.canonical_name,
            target_character_id=relationship.target_character_id,
            target_character_name=relationship.target_character.canonical_name,
            relationship_type=relationship.relationship_type,
            strength=relationship.strength,
            status=relationship.status,
            evidence=relationship.evidence,
        )

    def _relationship_counts(self, universe_id: uuid.UUID) -> dict[uuid.UUID, int]:
        statement = select(Relationship).where(Relationship.universe_id == universe_id)
        counts: dict[uuid.UUID, int] = {}
        for relationship in self._db.scalars(statement):
            counts[relationship.source_character_id] = (
                counts.get(relationship.source_character_id, 0) + 1
            )
            counts[relationship.target_character_id] = (
                counts.get(relationship.target_character_id, 0) + 1
            )
        return counts

    def _count(self, model: type[Any], universe_id: uuid.UUID) -> int:
        statement = select(func.count()).select_from(model).where(model.universe_id == universe_id)
        return int(self._db.scalar(statement) or 0)

    def _ensure_universe(self, universe_id: uuid.UUID) -> Universe:
        universe = self._db.get(Universe, universe_id)
        if universe is None:
            raise NotFoundError("Universe", universe_id)
        return universe
