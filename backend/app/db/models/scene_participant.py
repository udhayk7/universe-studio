from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.character import Character
    from app.db.models.scene import Scene


class SceneParticipant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scene_participants"
    __table_args__ = (
        UniqueConstraint(
            "scene_id", "character_id", "role", name="uq_scene_participants_scene_character_role"
        ),
        Index("ix_scene_participants_scene_id", "scene_id"),
        Index("ix_scene_participants_character_id", "character_id"),
    )

    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=False,
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False)

    scene: Mapped[Scene] = relationship("Scene", back_populates="participants")
    character: Mapped[Character] = relationship("Character", back_populates="scene_participants")
