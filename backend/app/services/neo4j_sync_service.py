from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from app.integrations.neo4j.connection import get_neo4j_manager
from app.integrations.neo4j.models import (
    CharacterNode,
    CommitNode,
    EventNode,
    GraphNode,
    LocationNode,
    ObjectNode,
    TimelineNode,
    UniverseNode,
)
from app.integrations.neo4j.relationships import (
    ALLIED_WITH,
    BETRAYED,
    CAUSED,
    KNOWS,
    LOVES,
    OCCURRED_AT,
    OWNS,
    PARTICIPATED_IN,
    RELATIONSHIP_TYPES,
    VISITED,
)
from app.repositories.graph_repository import GraphRepository
from app.services.universe_persistence_service import PersistenceResult

RELATIONSHIP_ALIASES = {
    "ALLIED_WITH": ALLIED_WITH,
    "ALLY": ALLIED_WITH,
    "ALLIES": ALLIED_WITH,
    "ASSOCIATE": KNOWS,
    "ASSOCIATES": KNOWS,
    "BETRAYS": BETRAYED,
    "BETRAYED": BETRAYED,
    "CAUSED": CAUSED,
    "CAUSES": CAUSED,
    "KNOWS": KNOWS,
    "LOVES": LOVES,
    "OWNS": OWNS,
    "PARTICIPATED_IN": PARTICIPATED_IN,
    "RIVAL": KNOWS,
    "RIVALS": KNOWS,
    "VISITED": VISITED,
    "VISITS": VISITED,
}


class Neo4jSyncService:
    def sync_extraction(self, result: PersistenceResult) -> None:
        manager = get_neo4j_manager()
        with manager.session() as session:
            repository = GraphRepository(session)

            universe_node = UniverseNode(
                id=result.universe.id,
                title=result.universe.title,
                genre=result.universe.genre,
                tone=result.universe.tone,
            ).graph_node
            timeline_node = TimelineNode(
                id=result.timeline.id,
                name=result.timeline.name,
                is_canon=result.timeline.is_canon,
                branch_from_commit_id=result.timeline.branch_from_commit_id,
            ).graph_node
            commit_node = CommitNode(
                id=result.commit.id,
                message=result.commit.message,
                commit_type=result.commit.commit_type,
            ).graph_node

            self._merge_node(repository, universe_node)
            self._merge_node(repository, self._with_universe_id(timeline_node, result.universe.id))
            self._merge_node(repository, self._with_universe_id(commit_node, result.universe.id))

            for character in result.characters:
                self._merge_node(
                    repository,
                    self._with_universe_id(
                        CharacterNode(
                            id=character.id,
                            name=character.canonical_name,
                            status=character.status,
                        ).graph_node,
                        result.universe.id,
                    ),
                )

            for location in result.locations:
                self._merge_node(
                    repository,
                    self._with_universe_id(
                        LocationNode(
                            id=location.id,
                            name=location.name,
                            location_type=location.location_type,
                        ).graph_node,
                        result.universe.id,
                    ),
                )

            for world_object in result.objects:
                self._merge_node(
                    repository,
                    self._with_universe_id(
                        ObjectNode(
                            id=world_object.id,
                            name=world_object.name,
                            object_type=world_object.object_type,
                            status=world_object.status,
                        ).graph_node,
                        result.universe.id,
                    ),
                )

            for event in result.events:
                self._merge_node(
                    repository,
                    self._with_universe_id(
                        EventNode(
                            id=event.id,
                            title=event.title,
                            event_type=event.event_type,
                            order_index=event.order_index,
                            importance=event.importance,
                        ).graph_node,
                        result.universe.id,
                    ),
                )

                for participant in event.participants:
                    self._merge_relationship(
                        repository,
                        from_label="Character",
                        from_id=participant.character_id,
                        to_label="Event",
                        to_id=event.id,
                        relationship_type=PARTICIPATED_IN,
                        properties={
                            "role": participant.role,
                            "universe_id": str(result.universe.id),
                        },
                    )

                if event.location_id:
                    self._merge_relationship(
                        repository,
                        from_label="Event",
                        from_id=event.id,
                        to_label="Location",
                        to_id=event.location_id,
                        relationship_type=OCCURRED_AT,
                        properties={"universe_id": str(result.universe.id)},
                    )

            for relationship in result.relationships:
                relationship_type = self._graph_relationship_type(relationship.relationship_type)
                self._merge_relationship(
                    repository,
                    from_label="Character",
                    from_id=relationship.source_character_id,
                    to_label="Character",
                    to_id=relationship.target_character_id,
                    relationship_type=relationship_type,
                    properties={
                        "universe_id": str(result.universe.id),
                        "timeline_id": str(result.timeline.id),
                        "strength": relationship.strength,
                        "source_type": relationship.relationship_type,
                    },
                )

    def _merge_node(self, repository: GraphRepository, node: GraphNode) -> None:
        labels = ":".join(node.labels)
        properties = self._serialize_properties(node.properties)
        query = f"MERGE (node:{labels} {{id: $id}}) SET node += $properties"
        repository.execute_write(query, {"id": str(node.id), "properties": properties})

    def _with_universe_id(self, node: GraphNode, universe_id: uuid.UUID) -> GraphNode:
        return GraphNode(
            id=node.id,
            labels=node.labels,
            properties={**node.properties, "universe_id": str(universe_id)},
        )

    def _merge_relationship(
        self,
        repository: GraphRepository,
        *,
        from_label: str,
        from_id: uuid.UUID,
        to_label: str,
        to_id: uuid.UUID,
        relationship_type: str,
        properties: Mapping[str, Any] | None = None,
    ) -> None:
        safe_type = self._graph_relationship_type(relationship_type)
        query = (
            f"MATCH (from_node:{from_label} {{id: $from_id}}), "
            f"(to_node:{to_label} {{id: $to_id}}) "
            f"MERGE (from_node)-[rel:{safe_type}]->(to_node) "
            "SET rel += $properties"
        )
        repository.execute_write(
            query,
            {
                "from_id": str(from_id),
                "to_id": str(to_id),
                "properties": self._serialize_properties(dict(properties or {})),
            },
        )

    def _graph_relationship_type(self, relationship_type: str) -> str:
        normalized = relationship_type.strip().upper().replace(" ", "_")
        resolved = RELATIONSHIP_ALIASES.get(normalized, normalized)
        return resolved if resolved in RELATIONSHIP_TYPES else KNOWS

    def _serialize_properties(self, properties: Mapping[str, Any]) -> dict[str, Any]:
        serialized: dict[str, Any] = {}
        for key, value in properties.items():
            if value is None:
                continue
            if isinstance(value, uuid.UUID):
                serialized[key] = str(value)
            else:
                serialized[key] = value
        return serialized
