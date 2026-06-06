from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.episode import Episode
    from app.db.models.scene import Scene
    from app.db.models.shot import Shot


class StoryboardImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "storyboard_images"
    __table_args__ = (
        Index("ix_storyboard_images_episode_id", "episode_id"),
        Index("ix_storyboard_images_scene_id", "scene_id"),
        Index("ix_storyboard_images_shot_id", "shot_id", unique=True),
        Index("ix_storyboard_images_status", "status"),
    )

    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("episodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=False,
    )
    shot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shots.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="generated")
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    revised_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    episode: Mapped[Episode] = relationship("Episode", back_populates="storyboard_images")
    scene: Mapped[Scene] = relationship("Scene", back_populates="storyboard_images")
    shot: Mapped[Shot] = relationship("Shot", back_populates="storyboard_image")
