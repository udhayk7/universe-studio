from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.episode import Episode
    from app.db.models.memory_entry import MemoryEntry
    from app.db.models.timeline import Timeline
    from app.db.models.timeline_commit_event import TimelineCommitEvent


class TimelineCommit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "timeline_commits"
    __table_args__ = (
        Index("ix_timeline_commits_timeline_id", "timeline_id"),
        Index("ix_timeline_commits_parent_commit_id", "parent_commit_id"),
        Index("ix_timeline_commits_commit_type", "commit_type"),
    )

    timeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("timelines.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_commit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("timeline_commits.id", ondelete="SET NULL"),
        nullable=True,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    commit_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")

    timeline: Mapped[Timeline] = relationship(
        "Timeline",
        back_populates="commits",
        foreign_keys=[timeline_id],
    )
    parent_commit: Mapped[TimelineCommit | None] = relationship(
        "TimelineCommit",
        remote_side="TimelineCommit.id",
        foreign_keys=[parent_commit_id],
    )
    commit_events: Mapped[list[TimelineCommitEvent]] = relationship(
        "TimelineCommitEvent",
        back_populates="commit",
        cascade="all, delete-orphan",
    )
    memory_entries: Mapped[list[MemoryEntry]] = relationship(
        "MemoryEntry",
        back_populates="commit",
        cascade="all, delete-orphan",
    )
    episodes: Mapped[list[Episode]] = relationship("Episode", back_populates="commit")
