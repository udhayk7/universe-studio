from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.character import Character
    from app.db.models.event import Event
    from app.db.models.timeline import Timeline
    from app.db.models.universe import Universe


class Relationship(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "relationships"
    __table_args__ = (
        CheckConstraint("strength IS NULL OR strength BETWEEN -100 AND 100", name="strength_range"),
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1", name="confidence_range"
        ),
        Index("ix_relationships_universe_id", "universe_id"),
        Index("ix_relationships_timeline_id", "timeline_id"),
        Index("ix_relationships_source_character_id", "source_character_id"),
        Index("ix_relationships_target_character_id", "target_character_id"),
        Index("ix_relationships_relationship_type", "relationship_type"),
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
    source_character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False)
    strength: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
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
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    universe: Mapped[Universe] = relationship("Universe", back_populates="relationships")
    timeline: Mapped[Timeline] = relationship("Timeline", back_populates="relationships")
    source_character: Mapped[Character] = relationship(
        "Character",
        foreign_keys=[source_character_id],
        back_populates="outgoing_relationships",
    )
    target_character: Mapped[Character] = relationship(
        "Character",
        foreign_keys=[target_character_id],
        back_populates="incoming_relationships",
    )
    valid_from_event: Mapped[Event | None] = relationship(
        "Event",
        foreign_keys=[valid_from_event_id],
        back_populates="relationships_started",
    )
    valid_to_event: Mapped[Event | None] = relationship(
        "Event",
        foreign_keys=[valid_to_event_id],
        back_populates="relationships_ended",
    )
