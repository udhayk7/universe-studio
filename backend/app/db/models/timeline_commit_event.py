from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.event import Event
    from app.db.models.timeline_commit import TimelineCommit


class TimelineCommitEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "timeline_commit_events"
    __table_args__ = (
        UniqueConstraint(
            "commit_id",
            "event_id",
            "change_type",
            name="uq_timeline_commit_events_commit_event_change",
        ),
        Index("ix_timeline_commit_events_commit_id", "commit_id"),
        Index("ix_timeline_commit_events_event_id", "event_id"),
    )

    commit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("timeline_commits.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    change_type: Mapped[str] = mapped_column(String(100), nullable=False)

    commit: Mapped[TimelineCommit] = relationship("TimelineCommit", back_populates="commit_events")
    event: Mapped[Event] = relationship("Event", back_populates="commit_events")
