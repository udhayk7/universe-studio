"""Initial Universe Studio persistence schema.

Revision ID: 202606070001
Revises:
Create Date: 2026-06-07 00:01:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "202606070001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UUID = postgresql.UUID(as_uuid=True)


def uuid_pk() -> sa.Column:
    return sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()"))


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    ]


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "universes",
        uuid_pk(),
        sa.Column("owner_id", UUID, nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("tagline", sa.String(length=500), nullable=True),
        sa.Column("premise", sa.Text(), nullable=True),
        sa.Column("genre", sa.String(length=100), nullable=True),
        sa.Column("tone", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        *timestamps(),
    )
    op.create_index("ix_universes_owner_id", "universes", ["owner_id"])
    op.create_index("ix_universes_status", "universes", ["status"])

    op.create_table(
        "assets",
        uuid_pk(),
        sa.Column("universe_id", UUID, nullable=False),
        sa.Column("storage_bucket", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("purpose", sa.String(length=100), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_assets_purpose", "assets", ["purpose"])
    op.create_index("ix_assets_universe_id", "assets", ["universe_id"])

    op.create_table(
        "locations",
        uuid_pk(),
        sa.Column("universe_id", UUID, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location_type", sa.String(length=100), nullable=True),
        sa.Column("rules", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *timestamps(),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_locations_location_type", "locations", ["location_type"])
    op.create_index("ix_locations_name", "locations", ["name"])
    op.create_index("ix_locations_universe_id", "locations", ["universe_id"])

    op.create_table(
        "characters",
        uuid_pk(),
        sa.Column("universe_id", UUID, nullable=False),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("aliases", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("traits", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("goals", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("fears", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("voice_style", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="unknown"),
        *timestamps(),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_characters_canonical_name", "characters", ["canonical_name"])
    op.create_index("ix_characters_status", "characters", ["status"])
    op.create_index("ix_characters_universe_id", "characters", ["universe_id"])

    op.create_table(
        "world_objects",
        uuid_pk(),
        sa.Column("universe_id", UUID, nullable=False),
        sa.Column("current_owner_character_id", UUID, nullable=True),
        sa.Column("current_location_id", UUID, nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("object_type", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        *timestamps(),
        sa.ForeignKeyConstraint(["current_location_id"], ["locations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["current_owner_character_id"], ["characters.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_world_objects_current_location_id", "world_objects", ["current_location_id"])
    op.create_index("ix_world_objects_current_owner_character_id", "world_objects", ["current_owner_character_id"])
    op.create_index("ix_world_objects_name", "world_objects", ["name"])
    op.create_index("ix_world_objects_object_type", "world_objects", ["object_type"])
    op.create_index("ix_world_objects_universe_id", "world_objects", ["universe_id"])

    op.create_table(
        "timelines",
        uuid_pk(),
        sa.Column("universe_id", UUID, nullable=False),
        sa.Column("parent_timeline_id", UUID, nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_canon", sa.Boolean(), nullable=False, server_default=sa.false()),
        *timestamps(),
        sa.ForeignKeyConstraint(["parent_timeline_id"], ["timelines.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_timelines_is_canon", "timelines", ["is_canon"])
    op.create_index("ix_timelines_parent_timeline_id", "timelines", ["parent_timeline_id"])
    op.create_index("ix_timelines_universe_id", "timelines", ["universe_id"])

    op.add_column("universes", sa.Column("active_timeline_id", UUID, nullable=True))
    op.create_foreign_key(
        "fk_universes_active_timeline_id_timelines",
        "universes",
        "timelines",
        ["active_timeline_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_universes_active_timeline_id", "universes", ["active_timeline_id"])

    op.create_table(
        "source_inputs",
        uuid_pk(),
        sa.Column("universe_id", UUID, nullable=False),
        sa.Column("asset_id", UUID, nullable=True),
        sa.Column("input_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="uploaded"),
        *timestamps(),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_source_inputs_asset_id", "source_inputs", ["asset_id"])
    op.create_index("ix_source_inputs_input_type", "source_inputs", ["input_type"])
    op.create_index("ix_source_inputs_universe_id", "source_inputs", ["universe_id"])

    op.create_table(
        "events",
        uuid_pk(),
        sa.Column("universe_id", UUID, nullable=False),
        sa.Column("location_id", UUID, nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=True),
        sa.Column("importance", sa.Integer(), nullable=True),
        *timestamps(),
        sa.CheckConstraint("importance IS NULL OR importance BETWEEN 1 AND 10", name="ck_events_importance_range"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_location_id", "events", ["location_id"])
    op.create_index("ix_events_order_index", "events", ["order_index"])
    op.create_index("ix_events_universe_id", "events", ["universe_id"])

    op.create_table(
        "event_participants",
        uuid_pk(),
        sa.Column("event_id", UUID, nullable=False),
        sa.Column("character_id", UUID, nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("event_id", "character_id", "role", name="uq_event_participants_event_character_role"),
    )
    op.create_index("ix_event_participants_character_id", "event_participants", ["character_id"])
    op.create_index("ix_event_participants_event_id", "event_participants", ["event_id"])

    op.create_table(
        "relationships",
        uuid_pk(),
        sa.Column("universe_id", UUID, nullable=False),
        sa.Column("timeline_id", UUID, nullable=False),
        sa.Column("source_character_id", UUID, nullable=False),
        sa.Column("target_character_id", UUID, nullable=False),
        sa.Column("relationship_type", sa.String(length=100), nullable=False),
        sa.Column("strength", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("valid_from_event_id", UUID, nullable=True),
        sa.Column("valid_to_event_id", UUID, nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        *timestamps(),
        sa.CheckConstraint("confidence IS NULL OR confidence BETWEEN 0 AND 1", name="ck_relationships_confidence_range"),
        sa.CheckConstraint("strength IS NULL OR strength BETWEEN -100 AND 100", name="ck_relationships_strength_range"),
        sa.ForeignKeyConstraint(["source_character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["timeline_id"], ["timelines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["valid_from_event_id"], ["events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["valid_to_event_id"], ["events.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_relationships_relationship_type", "relationships", ["relationship_type"])
    op.create_index("ix_relationships_source_character_id", "relationships", ["source_character_id"])
    op.create_index("ix_relationships_target_character_id", "relationships", ["target_character_id"])
    op.create_index("ix_relationships_timeline_id", "relationships", ["timeline_id"])
    op.create_index("ix_relationships_universe_id", "relationships", ["universe_id"])

    op.create_table(
        "timeline_commits",
        uuid_pk(),
        sa.Column("timeline_id", UUID, nullable=False),
        sa.Column("parent_commit_id", UUID, nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("commit_type", sa.String(length=100), nullable=False),
        sa.Column("created_by", sa.String(length=100), nullable=False, server_default="system"),
        *timestamps(),
        sa.ForeignKeyConstraint(["parent_commit_id"], ["timeline_commits.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["timeline_id"], ["timelines.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_timeline_commits_commit_type", "timeline_commits", ["commit_type"])
    op.create_index("ix_timeline_commits_parent_commit_id", "timeline_commits", ["parent_commit_id"])
    op.create_index("ix_timeline_commits_timeline_id", "timeline_commits", ["timeline_id"])

    op.add_column("timelines", sa.Column("branch_from_commit_id", UUID, nullable=True))
    op.add_column("timelines", sa.Column("head_commit_id", UUID, nullable=True))
    op.create_foreign_key(
        "fk_timelines_branch_from_commit_id_timeline_commits",
        "timelines",
        "timeline_commits",
        ["branch_from_commit_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_timelines_head_commit_id_timeline_commits",
        "timelines",
        "timeline_commits",
        ["head_commit_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_timelines_branch_from_commit_id", "timelines", ["branch_from_commit_id"])
    op.create_index("ix_timelines_head_commit_id", "timelines", ["head_commit_id"])

    op.create_table(
        "timeline_commit_events",
        uuid_pk(),
        sa.Column("commit_id", UUID, nullable=False),
        sa.Column("event_id", UUID, nullable=False),
        sa.Column("change_type", sa.String(length=100), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["commit_id"], ["timeline_commits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("commit_id", "event_id", "change_type", name="uq_timeline_commit_events_commit_event_change"),
    )
    op.create_index("ix_timeline_commit_events_commit_id", "timeline_commit_events", ["commit_id"])
    op.create_index("ix_timeline_commit_events_event_id", "timeline_commit_events", ["event_id"])

    op.create_table(
        "memory_entries",
        uuid_pk(),
        sa.Column("universe_id", UUID, nullable=False),
        sa.Column("timeline_id", UUID, nullable=False),
        sa.Column("commit_id", UUID, nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", UUID, nullable=True),
        sa.Column("memory_type", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("structured_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("valid_from_event_id", UUID, nullable=True),
        sa.Column("valid_to_event_id", UUID, nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        *timestamps(),
        sa.CheckConstraint("confidence IS NULL OR confidence BETWEEN 0 AND 1", name="ck_memory_entries_confidence_range"),
        sa.ForeignKeyConstraint(["commit_id"], ["timeline_commits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["timeline_id"], ["timelines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["valid_from_event_id"], ["events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["valid_to_event_id"], ["events.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_memory_entries_commit_id", "memory_entries", ["commit_id"])
    op.create_index("ix_memory_entries_entity", "memory_entries", ["entity_type", "entity_id"])
    op.create_index("ix_memory_entries_memory_type", "memory_entries", ["memory_type"])
    op.create_index("ix_memory_entries_timeline_id", "memory_entries", ["timeline_id"])
    op.create_index("ix_memory_entries_universe_id", "memory_entries", ["universe_id"])
    op.create_index(
        "ix_memory_entries_embedding_cosine",
        "memory_entries",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_memory_entries_structured_value_gin",
        "memory_entries",
        ["structured_value"],
        postgresql_using="gin",
    )

    op.create_table(
        "episodes",
        uuid_pk(),
        sa.Column("universe_id", UUID, nullable=False),
        sa.Column("timeline_id", UUID, nullable=False),
        sa.Column("commit_id", UUID, nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("logline", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        *timestamps(),
        sa.ForeignKeyConstraint(["commit_id"], ["timeline_commits.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["timeline_id"], ["timelines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_episodes_commit_id", "episodes", ["commit_id"])
    op.create_index("ix_episodes_status", "episodes", ["status"])
    op.create_index("ix_episodes_timeline_id", "episodes", ["timeline_id"])
    op.create_index("ix_episodes_universe_id", "episodes", ["universe_id"])

    op.create_table(
        "scenes",
        uuid_pk(),
        sa.Column("episode_id", UUID, nullable=False),
        sa.Column("location_id", UUID, nullable=True),
        sa.Column("scene_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("dialogue", sa.Text(), nullable=True),
        sa.Column("visual_direction", sa.Text(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("episode_id", "scene_number", name="uq_scenes_episode_scene_number"),
    )
    op.create_index("ix_scenes_episode_id", "scenes", ["episode_id"])
    op.create_index("ix_scenes_location_id", "scenes", ["location_id"])

    op.create_table(
        "scene_participants",
        uuid_pk(),
        sa.Column("scene_id", UUID, nullable=False),
        sa.Column("character_id", UUID, nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scene_id"], ["scenes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("scene_id", "character_id", "role", name="uq_scene_participants_scene_character_role"),
    )
    op.create_index("ix_scene_participants_character_id", "scene_participants", ["character_id"])
    op.create_index("ix_scene_participants_scene_id", "scene_participants", ["scene_id"])

    op.create_table(
        "jobs",
        uuid_pk(),
        sa.Column("universe_id", UUID, nullable=True),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint("progress BETWEEN 0 AND 100", name="ck_jobs_progress_range"),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_jobs_job_type", "jobs", ["job_type"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_universe_id", "jobs", ["universe_id"])

    op.create_table(
        "agent_runs",
        uuid_pk(),
        sa.Column("universe_id", UUID, nullable=True),
        sa.Column("job_id", UUID, nullable=True),
        sa.Column("agent_name", sa.String(length=255), nullable=False),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_agent_runs_agent_name", "agent_runs", ["agent_name"])
    op.create_index("ix_agent_runs_job_id", "agent_runs", ["job_id"])
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"])
    op.create_index("ix_agent_runs_universe_id", "agent_runs", ["universe_id"])

    op.create_table(
        "consistency_checks",
        uuid_pk(),
        sa.Column("universe_id", UUID, nullable=False),
        sa.Column("timeline_id", UUID, nullable=False),
        sa.Column("episode_id", UUID, nullable=True),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("issue_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("suggested_fix", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="open"),
        *timestamps(),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["timeline_id"], ["timelines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["universe_id"], ["universes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_consistency_checks_episode_id", "consistency_checks", ["episode_id"])
    op.create_index("ix_consistency_checks_severity", "consistency_checks", ["severity"])
    op.create_index("ix_consistency_checks_status", "consistency_checks", ["status"])
    op.create_index("ix_consistency_checks_timeline_id", "consistency_checks", ["timeline_id"])
    op.create_index("ix_consistency_checks_universe_id", "consistency_checks", ["universe_id"])


def downgrade() -> None:
    op.drop_table("consistency_checks")
    op.drop_table("agent_runs")
    op.drop_table("jobs")
    op.drop_table("scene_participants")
    op.drop_table("scenes")
    op.drop_table("episodes")
    op.drop_index("ix_memory_entries_structured_value_gin", table_name="memory_entries")
    op.drop_index("ix_memory_entries_embedding_cosine", table_name="memory_entries")
    op.drop_table("memory_entries")
    op.drop_table("timeline_commit_events")
    op.drop_constraint("fk_timelines_head_commit_id_timeline_commits", "timelines", type_="foreignkey")
    op.drop_constraint("fk_timelines_branch_from_commit_id_timeline_commits", "timelines", type_="foreignkey")
    op.drop_index("ix_timelines_head_commit_id", table_name="timelines")
    op.drop_index("ix_timelines_branch_from_commit_id", table_name="timelines")
    op.drop_column("timelines", "head_commit_id")
    op.drop_column("timelines", "branch_from_commit_id")
    op.drop_table("timeline_commits")
    op.drop_table("relationships")
    op.drop_table("event_participants")
    op.drop_table("events")
    op.drop_table("source_inputs")
    op.drop_constraint("fk_universes_active_timeline_id_timelines", "universes", type_="foreignkey")
    op.drop_index("ix_universes_active_timeline_id", table_name="universes")
    op.drop_column("universes", "active_timeline_id")
    op.drop_table("timelines")
    op.drop_table("world_objects")
    op.drop_table("characters")
    op.drop_table("locations")
    op.drop_table("assets")
    op.drop_table("universes")
