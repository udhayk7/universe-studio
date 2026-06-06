from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.episode import Episode
    from app.db.models.scene import Scene
    from app.db.models.storyboard_image import StoryboardImage


class Shot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shots"
    __table_args__ = (
        UniqueConstraint("scene_id", "shot_number", name="uq_shots_scene_shot_number"),
        Index("ix_shots_episode_id", "episode_id"),
        Index("ix_shots_scene_id", "scene_id"),
        Index("ix_shots_status", "status"),
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
    shot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    shot_type: Mapped[str] = mapped_column(String(100), nullable=False)
    camera_angle: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=8.0)
    visual_description: Mapped[str] = mapped_column(Text, nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="planned")

    episode: Mapped[Episode] = relationship("Episode", back_populates="shots")
    scene: Mapped[Scene] = relationship("Scene", back_populates="shots")
    storyboard_image: Mapped[StoryboardImage | None] = relationship(
        "StoryboardImage",
        back_populates="shot",
        cascade="all, delete-orphan",
        uselist=False,
    )
