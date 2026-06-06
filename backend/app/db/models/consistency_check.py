from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.episode import Episode
    from app.db.models.timeline import Timeline
    from app.db.models.universe import Universe


class ConsistencyCheck(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consistency_checks"
    __table_args__ = (
        Index("ix_consistency_checks_universe_id", "universe_id"),
        Index("ix_consistency_checks_timeline_id", "timeline_id"),
        Index("ix_consistency_checks_episode_id", "episode_id"),
        Index("ix_consistency_checks_severity", "severity"),
        Index("ix_consistency_checks_status", "status"),
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
    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("episodes.id", ondelete="CASCADE"),
        nullable=True,
    )
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_entities: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")

    universe: Mapped[Universe] = relationship("Universe", back_populates="consistency_checks")
    timeline: Mapped[Timeline] = relationship("Timeline")
    episode: Mapped[Episode | None] = relationship("Episode", back_populates="consistency_checks")
