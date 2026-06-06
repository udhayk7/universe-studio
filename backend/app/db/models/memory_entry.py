from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.timeline import Timeline
    from app.db.models.timeline_commit import TimelineCommit
    from app.db.models.universe import Universe


class MemoryEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memory_entries"
    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1", name="confidence_range"
        ),
        Index("ix_memory_entries_universe_id", "universe_id"),
        Index("ix_memory_entries_timeline_id", "timeline_id"),
        Index("ix_memory_entries_commit_id", "commit_id"),
        Index("ix_memory_entries_entity", "entity_type", "entity_id"),
        Index("ix_memory_entries_memory_type", "memory_type"),
    )

    universe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universes.id", ondelete="CASCADE"),
        nullable=False,
    )
    timeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("timelines.id", ondelete="CASCADE"),
        nullable=False,
    )
    commit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("timeline_commits.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    memory_type: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    valid_from_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="SET NULL"),
        nullable=True,
    )
    valid_to_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="SET NULL"),
        nullable=True,
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    universe: Mapped[Universe] = relationship("Universe", back_populates="memory_entries")
    timeline: Mapped[Timeline] = relationship("Timeline", back_populates="memory_entries")
    commit: Mapped[TimelineCommit] = relationship("TimelineCommit", back_populates="memory_entries")
