"""AI Skills & SDK tables — Sprint 36.8.

Revision ID: r1l234567890
Revises: q0k123456789
Create Date: 2026-08-03 22:05:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "r1l234567890"
down_revision: Union[str, None] = "q0k123456789"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts_cols():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("change_id", sa.String(length=64), nullable=True),
        sa.Column("source_client", sa.String(length=32), nullable=True),
        sa.Column("workspace_id", sa.String(length=128), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", JSONB(), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("skill_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("category", sa.String(64), nullable=False, server_default="analysis"),
        sa.Column("latest_version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("visibility", sa.String(32), nullable=False, server_default="enterprise"),
        sa.Column("tags_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("signature", sa.String(128), nullable=False, server_default=""),
        sa.Column("author", sa.String(128), nullable=False, server_default="platform"),
        sa.Column("rating", sa.Float(), nullable=False, server_default="0"),
        sa.Column("ratings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("changelog_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("skill_key", name="uq_skills_skill_key"),
    )
    op.create_index("ix_skills_category", "skills", ["category"])
    op.create_index("ix_skills_visibility", "skills", ["visibility"])

    op.create_table(
        "skill_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("version_key", sa.String(64), nullable=False),
        sa.Column("skill_key", sa.String(128), nullable=False),
        sa.Column("semver", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("changelog", sa.Text(), nullable=False, server_default=""),
        sa.Column("signature", sa.String(128), nullable=False, server_default=""),
        sa.Column("manifest_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("skill_key", "semver", name="uq_skill_versions_skill_semver"),
    )
    op.create_index("ix_skill_versions_skill_key", "skill_versions", ["skill_key"])

    op.create_table(
        "skill_dependencies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("skill_key", sa.String(128), nullable=False),
        sa.Column("depends_on_key", sa.String(128), nullable=False),
        sa.Column("constraint_kind", sa.String(64), nullable=False, server_default="required"),
        *_ts_cols(),
    )
    op.create_index("ix_skill_dependencies_skill_key", "skill_dependencies", ["skill_key"])

    op.create_table(
        "skill_permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("skill_key", sa.String(128), nullable=False),
        sa.Column("permission", sa.String(128), nullable=False),
        sa.Column("principal", sa.String(128), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_skill_permissions_skill_key", "skill_permissions", ["skill_key"])

    op.create_table(
        "installed_skills",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("install_key", sa.String(64), nullable=False),
        sa.Column("skill_key", sa.String(128), nullable=False),
        sa.Column("semver", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("state", sa.String(32), nullable=False, server_default="enabled"),
        sa.Column("principal", sa.String(128), nullable=False, server_default="system"),
        sa.Column("sandbox", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("resource_limits_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("skill_key", "principal", name="uq_installed_skills_skill_principal"),
    )
    op.create_index("ix_installed_skills_state", "installed_skills", ["state"])

    op.create_table(
        "skill_statistics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("metric_key", sa.String(128), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("details_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("note", sa.Text(), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_skill_statistics_metric_key", "skill_statistics", ["metric_key"])

    op.create_table(
        "skill_marketplace",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_key", sa.String(64), nullable=False),
        sa.Column("skill_key", sa.String(128), nullable=False),
        sa.Column("repository", sa.String(32), nullable=False, server_default="enterprise"),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating", sa.Float(), nullable=False, server_default="0"),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("skill_key", name="uq_skill_marketplace_skill_key"),
    )
    op.create_index("ix_skill_marketplace_repository", "skill_marketplace", ["repository"])


def downgrade() -> None:
    for table in (
        "skill_marketplace",
        "skill_statistics",
        "installed_skills",
        "skill_permissions",
        "skill_dependencies",
        "skill_versions",
        "skills",
    ):
        op.drop_table(table)
