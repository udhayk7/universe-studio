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
    from app.db.models.universe import Universe


class SourceInput(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_inputs"
    __table_args__ = (
        Index("ix_source_inputs_universe_id", "universe_id"),
        Index("ix_source_inputs_asset_id", "asset_id"),
        Index("ix_source_inputs_input_type", "input_type"),
    )

    universe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universes.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    input_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="uploaded")

    universe: Mapped[Universe] = relationship("Universe", back_populates="source_inputs")
    asset: Mapped[Asset | None] = relationship("Asset", back_populates="source_inputs")
