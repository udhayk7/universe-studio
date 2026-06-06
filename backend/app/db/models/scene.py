from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.episode import Episode
    from app.db.models.location import Location
    from app.db.models.scene_participant import SceneParticipant
    from app.db.models.shot import Shot
    from app.db.models.storyboard_image import StoryboardImage


class Scene(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scenes"
    __table_args__ = (
        UniqueConstraint("episode_id", "scene_number", name="uq_scenes_episode_scene_number"),
        Index("ix_scenes_episode_id", "episode_id"),
        Index("ix_scenes_location_id", "location_id"),
    )

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("episodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
    )
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    dialogue: Mapped[str | None] = mapped_column(Text, nullable=True)
    visual_direction: Mapped[str | None] = mapped_column(Text, nullable=True)

    episode: Mapped[Episode] = relationship("Episode", back_populates="scenes")
    location: Mapped[Location | None] = relationship("Location", back_populates="scenes")
    participants: Mapped[list[SceneParticipant]] = relationship(
        "SceneParticipant",
        back_populates="scene",
        cascade="all, delete-orphan",
    )
    shots: Mapped[list[Shot]] = relationship(
        "Shot",
        back_populates="scene",
        cascade="all, delete-orphan",
    )
    storyboard_images: Mapped[list[StoryboardImage]] = relationship(
        "StoryboardImage",
        back_populates="scene",
        cascade="all, delete-orphan",
    )
