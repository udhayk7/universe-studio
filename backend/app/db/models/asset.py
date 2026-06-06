from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.source_input import SourceInput
    from app.db.models.universe import Universe


class Asset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (
        Index("ix_assets_universe_id", "universe_id"),
        Index("ix_assets_purpose", "purpose"),
    )

    universe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universes.id", ondelete="CASCADE"),
        nullable=False,
    )
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    purpose: Mapped[str] = mapped_column(String(100), nullable=False)

    universe: Mapped[Universe] = relationship("Universe", back_populates="assets")
    source_inputs: Mapped[list[SourceInput]] = relationship(
        "SourceInput",
        back_populates="asset",
    )
