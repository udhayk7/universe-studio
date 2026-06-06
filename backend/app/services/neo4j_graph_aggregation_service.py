from __future__ import annotations

import uuid
from typing import Any

from app.integrations.neo4j.connection import get_neo4j_manager
from app.repositories.graph_repository import GraphRepository
from app.schemas.memory_explorer import MemoryGraphEdge, MemoryGraphNode, UniverseGraphResponse

GRAPH_NODE_LABELS = frozenset({"Character", "Event", "Location", "Object"})


class Neo4jGraphAggregationService:
    def get_graph(self, universe_id: uuid.UUID) -> UniverseGraphResponse:
        manager = get_neo4j_manager()
        with manager.session() as session:
            repository = GraphRepository(session)
            records = repository.execute_read(
                """
                MATCH (u:Universe {id: $universe_id})
                OPTIONAL MATCH (n)
                WHERE n.universe_id = $universe_id
                  AND any(label IN labels(n) WHERE label IN $graph_labels)
                OPTIONAL MATCH (a)-[r]->(b)
                WHERE r.universe_id = $universe_id
                WITH collect(DISTINCT n) + collect(DISTINCT a) + collect(DISTINCT b) AS raw_nodes,
                     collect(DISTINCT r) AS relationships
                UNWIND raw_nodes AS node
                WITH collect(DISTINCT node) AS nodes, relationships
                RETURN
                  [node IN nodes WHERE node IS NOT NULL | {
                    id: node.id,
                    labels: labels(node),
                    properties: properties(node)
                  }] AS nodes,
                  [rel IN relationships WHERE rel IS NOT NULL | {
                    id: elementId(rel),
                    source: startNode(rel).id,
                    target: endNode(rel).id,
                    type: type(rel),
                    properties: properties(rel)
                  }] AS edges
                """,
                {
                    "universe_id": str(universe_id),
                    "graph_labels": list(GRAPH_NODE_LABELS),
                },
            )

        if not records:
            return UniverseGraphResponse(
                universe_id=universe_id,
                source="neo4j",
                nodes=[],
                edges=[],
            )

        record = records[0]
        nodes = [self._node_from_record(node) for node in record.get("nodes", [])]
        edges = [self._edge_from_record(edge) for edge in record.get("edges", [])]
        return UniverseGraphResponse(
            universe_id=universe_id,
            source="neo4j",
            nodes=nodes,
            edges=edges,
        )

    def _node_from_record(self, node: dict[str, Any]) -> MemoryGraphNode:
        labels = set(node.get("labels", []))
        properties = dict(node.get("properties", {}))
        node_type = self._node_type(labels)
        label = (
            properties.get("name")
            or properties.get("title")
            or properties.get("label")
            or str(node["id"])
        )
        subtitle = (
            properties.get("status")
            or properties.get("location_type")
            or properties.get("object_type")
        )
        return MemoryGraphNode(
            id=str(node["id"]),
            type=node_type,
            label=str(label),
            subtitle=str(subtitle) if subtitle is not None else None,
            properties=properties,
        )

    def _edge_from_record(self, edge: dict[str, Any]) -> MemoryGraphEdge:
        properties = dict(edge.get("properties", {}))
        return MemoryGraphEdge(
            id=str(edge["id"]),
            source=str(edge["source"]),
            target=str(edge["target"]),
            type=str(edge["type"]),
            label=str(edge["type"]).replace("_", " ").title(),
            strength=properties.get("strength"),
            properties=properties,
        )

    def _node_type(self, labels: set[str]) -> str:
        if "Character" in labels:
            return "character"
        if "Event" in labels:
            return "event"
        if "Location" in labels:
            return "location"
        return "object"
