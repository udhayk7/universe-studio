from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.character import Character
    from app.db.models.location import Location
    from app.db.models.universe import Universe


class WorldObject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "world_objects"
    __table_args__ = (
        Index("ix_world_objects_universe_id", "universe_id"),
        Index("ix_world_objects_name", "name"),
        Index("ix_world_objects_object_type", "object_type"),
        Index("ix_world_objects_current_owner_character_id", "current_owner_character_id"),
        Index("ix_world_objects_current_location_id", "current_location_id"),
    )

    universe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universes.id", ondelete="CASCADE"),
        nullable=False,
    )
    current_owner_character_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    object_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    universe: Mapped[Universe] = relationship("Universe", back_populates="world_objects")
    current_owner: Mapped[Character | None] = relationship(
        "Character",
        back_populates="owned_objects",
        foreign_keys=[current_owner_character_id],
    )
    current_location: Mapped[Location | None] = relationship(
        "Location",
        back_populates="world_objects",
        foreign_keys=[current_location_id],
    )
