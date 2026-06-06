from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class GraphNode:
    id: uuid.UUID
    labels: tuple[str, ...]
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class UniverseNode:
    id: uuid.UUID
    title: str
    genre: str | None = None
    tone: str | None = None

    @property
    def graph_node(self) -> GraphNode:
        return GraphNode(
            id=self.id,
            labels=("Universe",),
            properties={"title": self.title, "genre": self.genre, "tone": self.tone},
        )


@dataclass(frozen=True, slots=True)
class TimelineNode:
    id: uuid.UUID
    name: str
    is_canon: bool
    branch_from_commit_id: uuid.UUID | None = None

    @property
    def graph_node(self) -> GraphNode:
        return GraphNode(
            id=self.id,
            labels=("Timeline",),
            properties={
                "name": self.name,
                "is_canon": self.is_canon,
                "branch_from_commit_id": str(self.branch_from_commit_id)
                if self.branch_from_commit_id
                else None,
            },
        )


@dataclass(frozen=True, slots=True)
class CommitNode:
    id: uuid.UUID
    message: str
    commit_type: str

    @property
    def graph_node(self) -> GraphNode:
        return GraphNode(
            id=self.id,
            labels=("Commit",),
            properties={"message": self.message, "commit_type": self.commit_type},
        )


@dataclass(frozen=True, slots=True)
class CharacterNode:
    id: uuid.UUID
    name: str
    status: str

    @property
    def graph_node(self) -> GraphNode:
        return GraphNode(
            id=self.id,
            labels=("Character",),
            properties={"name": self.name, "status": self.status},
        )


@dataclass(frozen=True, slots=True)
class EventNode:
    id: uuid.UUID
    title: str
    event_type: str | None = None
    order_index: int | None = None
    importance: int | None = None

    @property
    def graph_node(self) -> GraphNode:
        return GraphNode(
            id=self.id,
            labels=("Event",),
            properties={
                "title": self.title,
                "event_type": self.event_type,
                "order_index": self.order_index,
                "importance": self.importance,
            },
        )


@dataclass(frozen=True, slots=True)
class LocationNode:
    id: uuid.UUID
    name: str
    location_type: str | None = None

    @property
    def graph_node(self) -> GraphNode:
        return GraphNode(
            id=self.id,
            labels=("Location",),
            properties={"name": self.name, "location_type": self.location_type},
        )


@dataclass(frozen=True, slots=True)
class ObjectNode:
    id: uuid.UUID
    name: str
    object_type: str | None = None
    status: str | None = None

    @property
    def graph_node(self) -> GraphNode:
        return GraphNode(
            id=self.id,
            labels=("Object",),
            properties={"name": self.name, "object_type": self.object_type, "status": self.status},
        )
