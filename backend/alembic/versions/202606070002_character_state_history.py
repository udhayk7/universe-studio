"""Add character state history.

Revision ID: 202606070002
Revises: 202606070001
Create Date: 2026-06-07 00:02:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202606070002"
down_revision: str | None = "202606070001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "character_state_history",
        sa.Column(
            "id",
            UUID,
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("universe_id", UUID, nullable=False),
        sa.Column("character_id", UUID, nullable=False),
        sa.Column("timeline_id", UUID, nullable=False),
        sa.Column("commit_id", UUID, nullable=False),
        sa.Column("location_id", UUID, nullable=True),
        sa.Column(
            "current_status",
            sa.String(length=50),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column("emotional_state", sa.String(length=100), nullable=True),
        sa.Column("physical_state", sa.String(length=100), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False, server_default="system"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name="character_state_confidence_range",
        ),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["timeline_id"], ["timelines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["commit_id"], ["timeline_commits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_character_state_history_universe_id",
        "character_state_history",
        ["universe_id"],
    )
    op.create_index(
        "ix_character_state_history_character_id",
        "character_state_history",
        ["character_id"],
    )
    op.create_index(
        "ix_character_state_history_timeline_id",
        "character_state_history",
        ["timeline_id"],
    )
    op.create_index(
        "ix_character_state_history_commit_id",
        "character_state_history",
        ["commit_id"],
    )
    op.create_index(
        "ix_character_state_history_current_status",
        "character_state_history",
        ["current_status"],
    )
    op.create_index(
        "ix_character_state_history_emotional_state",
        "character_state_history",
        ["emotional_state"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_character_state_history_emotional_state",
        table_name="character_state_history",
    )
    op.drop_index(
        "ix_character_state_history_current_status",
        table_name="character_state_history",
    )
    op.drop_index("ix_character_state_history_commit_id", table_name="character_state_history")
    op.drop_index(
        "ix_character_state_history_timeline_id",
        table_name="character_state_history",
    )
    op.drop_index(
        "ix_character_state_history_character_id",
        table_name="character_state_history",
    )
    op.drop_index(
        "ix_character_state_history_universe_id",
        table_name="character_state_history",
    )
    op.drop_table("character_state_history")
