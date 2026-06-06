from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.consistency_check import ConsistencyCheck
    from app.db.models.scene import Scene
    from app.db.models.timeline import Timeline
    from app.db.models.timeline_commit import TimelineCommit
    from app.db.models.universe import Universe


class Episode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "episodes"
    __table_args__ = (
        Index("ix_episodes_universe_id", "universe_id"),
        Index("ix_episodes_timeline_id", "timeline_id"),
        Index("ix_episodes_commit_id", "commit_id"),
        Index("ix_episodes_status", "status"),
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
    commit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("timeline_commits.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    logline: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")

    universe: Mapped[Universe] = relationship("Universe", back_populates="episodes")
    timeline: Mapped[Timeline] = relationship("Timeline", back_populates="episodes")
    commit: Mapped[TimelineCommit | None] = relationship(
        "TimelineCommit", back_populates="episodes"
    )
    scenes: Mapped[list[Scene]] = relationship(
        "Scene",
        back_populates="episode",
        cascade="all, delete-orphan",
    )
    consistency_checks: Mapped[list[ConsistencyCheck]] = relationship(
        "ConsistencyCheck",
        back_populates="episode",
    )
