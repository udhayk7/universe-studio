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
    from app.db.models.event import Event


class EventParticipant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "event_participants"
    __table_args__ = (
        UniqueConstraint(
            "event_id", "character_id", "role", name="uq_event_participants_event_character_role"
        ),
        Index("ix_event_participants_event_id", "event_id"),
        Index("ix_event_participants_character_id", "character_id"),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False)

    event: Mapped[Event] = relationship("Event", back_populates="participants")
    character: Mapped[Character] = relationship("Character", back_populates="event_participants")
