"""Add cinematic shots and storyboard images.

Revision ID: 202606070005
Revises: 202606070004
Create Date: 2026-06-07 04:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202606070005"
down_revision: str | None = "202606070004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)


def uuid_pk() -> sa.Column:
    return sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()"))


def timestamps() -> list[sa.Column]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "shots",
        uuid_pk(),
        sa.Column("episode_id", UUID, nullable=False),
        sa.Column("scene_id", UUID, nullable=False),
        sa.Column("shot_number", sa.Integer(), nullable=False),
        sa.Column("shot_type", sa.String(length=100), nullable=False),
        sa.Column("camera_angle", sa.String(length=100), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("visual_description", sa.Text(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="planned"),
        *timestamps(),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("scene_id", "shot_number", name="uq_shots_scene_shot_number"),
    )
    op.create_index("ix_shots_episode_id", "shots", ["episode_id"])
    op.create_index("ix_shots_scene_id", "shots", ["scene_id"])
    op.create_index("ix_shots_status", "shots", ["status"])

    op.create_table(
        "storyboard_images",
        uuid_pk(),
        sa.Column("episode_id", UUID, nullable=False),
        sa.Column("scene_id", UUID, nullable=False),
        sa.Column("shot_id", UUID, nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="generated"),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("image_data", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("revised_prompt", sa.Text(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shot_id"], ["shots.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_storyboard_images_episode_id", "storyboard_images", ["episode_id"])
    op.create_index("ix_storyboard_images_scene_id", "storyboard_images", ["scene_id"])
    op.create_index(
        "ix_storyboard_images_shot_id",
        "storyboard_images",
        ["shot_id"],
        unique=True,
    )
    op.create_index("ix_storyboard_images_status", "storyboard_images", ["status"])


def downgrade() -> None:
    op.drop_index("ix_storyboard_images_status", table_name="storyboard_images")
    op.drop_index("ix_storyboard_images_shot_id", table_name="storyboard_images")
    op.drop_index("ix_storyboard_images_scene_id", table_name="storyboard_images")
    op.drop_index("ix_storyboard_images_episode_id", table_name="storyboard_images")
    op.drop_table("storyboard_images")
    op.drop_index("ix_shots_status", table_name="shots")
    op.drop_index("ix_shots_scene_id", table_name="shots")
    op.drop_index("ix_shots_episode_id", table_name="shots")
    op.drop_table("shots")
