from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.asset import Asset
    from app.db.models.character import Character
    from app.db.models.consistency_check import ConsistencyCheck
    from app.db.models.episode import Episode
    from app.db.models.event import Event
    from app.db.models.job import Job
    from app.db.models.location import Location
    from app.db.models.memory_entry import MemoryEntry
    from app.db.models.relationship import Relationship
    from app.db.models.source_input import SourceInput
    from app.db.models.timeline import Timeline
    from app.db.models.world_object import WorldObject


class Universe(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "universes"
    __table_args__ = (
        Index("ix_universes_status", "status"),
        Index("ix_universes_owner_id", "owner_id"),
    )

    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    active_timeline_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("timelines.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    tagline: Mapped[str | None] = mapped_column(String(500), nullable=True)
    premise: Mapped[str | None] = mapped_column(Text, nullable=True)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")

    active_timeline: Mapped[Timeline | None] = relationship(
        "Timeline",
        foreign_keys=[active_timeline_id],
        post_update=True,
    )
    assets: Mapped[list[Asset]] = relationship(
        "Asset",
        back_populates="universe",
        cascade="all, delete-orphan",
    )
    source_inputs: Mapped[list[SourceInput]] = relationship(
        "SourceInput",
        back_populates="universe",
        cascade="all, delete-orphan",
    )
    characters: Mapped[list[Character]] = relationship(
        "Character",
        back_populates="universe",
        cascade="all, delete-orphan",
    )
    locations: Mapped[list[Location]] = relationship(
        "Location",
        back_populates="universe",
        cascade="all, delete-orphan",
    )
    world_objects: Mapped[list[WorldObject]] = relationship(
        "WorldObject",
        back_populates="universe",
        cascade="all, delete-orphan",
    )
    relationships: Mapped[list[Relationship]] = relationship(
        "Relationship",
        back_populates="universe",
        cascade="all, delete-orphan",
    )
    events: Mapped[list[Event]] = relationship(
        "Event",
        back_populates="universe",
        cascade="all, delete-orphan",
    )
    timelines: Mapped[list[Timeline]] = relationship(
        "Timeline",
        back_populates="universe",
        cascade="all, delete-orphan",
        foreign_keys="Timeline.universe_id",
    )
    memory_entries: Mapped[list[MemoryEntry]] = relationship(
        "MemoryEntry",
        back_populates="universe",
        cascade="all, delete-orphan",
    )
    episodes: Mapped[list[Episode]] = relationship(
        "Episode",
        back_populates="universe",
        cascade="all, delete-orphan",
    )
    consistency_checks: Mapped[list[ConsistencyCheck]] = relationship(
        "ConsistencyCheck",
        back_populates="universe",
        cascade="all, delete-orphan",
    )
    jobs: Mapped[list[Job]] = relationship(
        "Job",
        back_populates="universe",
        cascade="all, delete-orphan",
    )
