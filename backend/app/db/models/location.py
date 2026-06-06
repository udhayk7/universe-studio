from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.event import Event
    from app.db.models.scene import Scene
    from app.db.models.universe import Universe
    from app.db.models.world_object import WorldObject


class Location(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "locations"
    __table_args__ = (
        Index("ix_locations_universe_id", "universe_id"),
        Index("ix_locations_name", "name"),
        Index("ix_locations_location_type", "location_type"),
    )

    universe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universes.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    universe: Mapped[Universe] = relationship("Universe", back_populates="locations")
    events: Mapped[list[Event]] = relationship("Event", back_populates="location")
    scenes: Mapped[list[Scene]] = relationship("Scene", back_populates="location")
    world_objects: Mapped[list[WorldObject]] = relationship(
        "WorldObject",
        back_populates="current_location",
        foreign_keys="WorldObject.current_location_id",
    )
