from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.episode import Episode
    from app.db.models.memory_entry import MemoryEntry
    from app.db.models.relationship import Relationship
    from app.db.models.timeline_commit import TimelineCommit
    from app.db.models.universe import Universe


class Timeline(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "timelines"
    __table_args__ = (
        Index("ix_timelines_universe_id", "universe_id"),
        Index("ix_timelines_parent_timeline_id", "parent_timeline_id"),
        Index("ix_timelines_branch_from_commit_id", "branch_from_commit_id"),
        Index("ix_timelines_head_commit_id", "head_commit_id"),
        Index("ix_timelines_is_canon", "is_canon"),
    )

    universe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universes.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_timeline_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("timelines.id", ondelete="SET NULL"),
        nullable=True,
    )
    branch_from_commit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("timeline_commits.id", ondelete="SET NULL"),
        nullable=True,
    )
    head_commit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("timeline_commits.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_canon: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    universe: Mapped[Universe] = relationship(
        "Universe",
        back_populates="timelines",
        foreign_keys=[universe_id],
    )
    parent_timeline: Mapped[Timeline | None] = relationship(
        "Timeline",
        remote_side="Timeline.id",
        foreign_keys=[parent_timeline_id],
    )
    branch_from_commit: Mapped[TimelineCommit | None] = relationship(
        "TimelineCommit",
        foreign_keys=[branch_from_commit_id],
        post_update=True,
    )
    head_commit: Mapped[TimelineCommit | None] = relationship(
        "TimelineCommit",
        foreign_keys=[head_commit_id],
        post_update=True,
    )
    commits: Mapped[list[TimelineCommit]] = relationship(
        "TimelineCommit",
        back_populates="timeline",
        cascade="all, delete-orphan",
        foreign_keys="TimelineCommit.timeline_id",
    )
    relationships: Mapped[list[Relationship]] = relationship(
        "Relationship",
        back_populates="timeline",
        cascade="all, delete-orphan",
    )
    memory_entries: Mapped[list[MemoryEntry]] = relationship(
        "MemoryEntry",
        back_populates="timeline",
        cascade="all, delete-orphan",
    )
    episodes: Mapped[list[Episode]] = relationship(
        "Episode",
        back_populates="timeline",
        cascade="all, delete-orphan",
    )
