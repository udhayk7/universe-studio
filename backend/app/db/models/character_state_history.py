from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.character import Character
    from app.db.models.location import Location
    from app.db.models.timeline import Timeline
    from app.db.models.timeline_commit import TimelineCommit
    from app.db.models.universe import Universe


class CharacterStateHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "character_state_history"
    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name="character_state_confidence_range",
        ),
        Index("ix_character_state_history_universe_id", "universe_id"),
        Index("ix_character_state_history_character_id", "character_id"),
        Index("ix_character_state_history_timeline_id", "timeline_id"),
        Index("ix_character_state_history_commit_id", "commit_id"),
        Index("ix_character_state_history_current_status", "current_status"),
        Index("ix_character_state_history_emotional_state", "emotional_state"),
    )

    universe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universes.id", ondelete="CASCADE"),
        nullable=False,
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
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
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_status: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    emotional_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    physical_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    universe: Mapped[Universe] = relationship("Universe")
    character: Mapped[Character] = relationship("Character", back_populates="state_history")
    timeline: Mapped[Timeline] = relationship("Timeline")
    commit: Mapped[TimelineCommit] = relationship("TimelineCommit")
    location: Mapped[Location | None] = relationship("Location")
