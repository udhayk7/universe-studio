from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202606070004"
down_revision: str | None = "202606070003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agent_runs",
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("agent_runs", sa.Column("duration_ms", sa.Integer(), nullable=True))
    op.create_index("ix_agent_runs_episode_id", "agent_runs", ["episode_id"])
    op.create_foreign_key(
        "fk_agent_runs_episode_id_episodes",
        "agent_runs",
        "episodes",
        ["episode_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.add_column(
        "consistency_checks",
        sa.Column(
            "affected_entities",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.alter_column("consistency_checks", "affected_entities", server_default=None)


def downgrade() -> None:
    op.drop_column("consistency_checks", "affected_entities")
    op.drop_constraint("fk_agent_runs_episode_id_episodes", "agent_runs", type_="foreignkey")
    op.drop_index("ix_agent_runs_episode_id", table_name="agent_runs")
    op.drop_column("agent_runs", "duration_ms")
    op.drop_column("agent_runs", "episode_id")
