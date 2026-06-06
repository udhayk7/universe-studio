from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.event_participant import EventParticipant
    from app.db.models.location import Location
    from app.db.models.relationship import Relationship
    from app.db.models.timeline_commit_event import TimelineCommitEvent
    from app.db.models.universe import Universe


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "importance IS NULL OR importance BETWEEN 1 AND 10", name="importance_range"
        ),
        Index("ix_events_universe_id", "universe_id"),
        Index("ix_events_location_id", "location_id"),
        Index("ix_events_event_type", "event_type"),
        Index("ix_events_order_index", "order_index"),
    )

    universe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universes.id", ondelete="CASCADE"),
        nullable=False,
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    importance: Mapped[int | None] = mapped_column(Integer, nullable=True)

    universe: Mapped[Universe] = relationship("Universe", back_populates="events")
    location: Mapped[Location | None] = relationship("Location", back_populates="events")
    participants: Mapped[list[EventParticipant]] = relationship(
        "EventParticipant",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    commit_events: Mapped[list[TimelineCommitEvent]] = relationship(
        "TimelineCommitEvent",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    relationships_started: Mapped[list[Relationship]] = relationship(
        "Relationship",
        foreign_keys="Relationship.valid_from_event_id",
        back_populates="valid_from_event",
    )
    relationships_ended: Mapped[list[Relationship]] = relationship(
        "Relationship",
        foreign_keys="Relationship.valid_to_event_id",
        back_populates="valid_to_event",
    )
