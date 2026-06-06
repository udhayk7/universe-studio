from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.character_state_history import CharacterStateHistory
    from app.db.models.event_participant import EventParticipant
    from app.db.models.relationship import Relationship
    from app.db.models.scene_participant import SceneParticipant
    from app.db.models.universe import Universe
    from app.db.models.world_object import WorldObject


class Character(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "characters"
    __table_args__ = (
        Index("ix_characters_universe_id", "universe_id"),
        Index("ix_characters_canonical_name", "canonical_name"),
        Index("ix_characters_status", "status"),
    )

    universe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universes.id", ondelete="CASCADE"),
        nullable=False,
    )
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    traits: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    goals: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    fears: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    voice_style: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")

    universe: Mapped[Universe] = relationship("Universe", back_populates="characters")
    event_participants: Mapped[list[EventParticipant]] = relationship(
        "EventParticipant",
        back_populates="character",
        cascade="all, delete-orphan",
    )
    scene_participants: Mapped[list[SceneParticipant]] = relationship(
        "SceneParticipant",
        back_populates="character",
        cascade="all, delete-orphan",
    )
    state_history: Mapped[list[CharacterStateHistory]] = relationship(
        "CharacterStateHistory",
        back_populates="character",
        cascade="all, delete-orphan",
    )
    outgoing_relationships: Mapped[list[Relationship]] = relationship(
        "Relationship",
        foreign_keys="Relationship.source_character_id",
        back_populates="source_character",
        cascade="all, delete-orphan",
    )
    incoming_relationships: Mapped[list[Relationship]] = relationship(
        "Relationship",
        foreign_keys="Relationship.target_character_id",
        back_populates="target_character",
        cascade="all, delete-orphan",
    )
    owned_objects: Mapped[list[WorldObject]] = relationship(
        "WorldObject",
        back_populates="current_owner",
        foreign_keys="WorldObject.current_owner_character_id",
    )
