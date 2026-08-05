"""Creative Factory tables — Sprint 36.9.

Revision ID: s2m345678901
Revises: r1l234567890
Create Date: 2026-08-04 08:50:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "s2m345678901"
down_revision: Union[str, None] = "r1l234567890"
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
        "creative_projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("brand_id", sa.String(128), nullable=True),
        sa.Column("asset_ids_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("campaign_ids_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("project_key", name="uq_creative_projects_project_key"),
    )
    op.create_index("ix_creative_projects_brand_id", "creative_projects", ["brand_id"])

    op.create_table(
        "creative_assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_key", sa.String(128), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("creative_type", sa.String(64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("modality", sa.String(64), nullable=False, server_default="text"),
        sa.Column("project_id", sa.String(128), nullable=True),
        sa.Column("brand_id", sa.String(128), nullable=True),
        sa.Column("template_id", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("media_url", sa.String(512), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("provider_id", sa.String(128), nullable=True),
        sa.Column("asset_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tags_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("embedding_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("asset_key", name="uq_creative_assets_asset_key"),
    )
    op.create_index("ix_creative_assets_type", "creative_assets", ["creative_type"])
    op.create_index("ix_creative_assets_status", "creative_assets", ["status"])
    op.create_index("ix_creative_assets_project_id", "creative_assets", ["project_id"])

    op.create_table(
        "creative_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("template_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("creative_type", sa.String(64), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("brand_id", sa.String(128), nullable=True),
        sa.Column("channels_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("variables_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("template_key", name="uq_creative_templates_template_key"),
    )
    op.create_index("ix_creative_templates_type", "creative_templates", ["creative_type"])

    op.create_table(
        "campaigns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("objective", sa.String(128), nullable=False, server_default="awareness"),
        sa.Column("audience", sa.String(256), nullable=False, server_default="general"),
        sa.Column("channels_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("budget", sa.Float(), nullable=False, server_default="0"),
        sa.Column("creative_ids_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("schedule_at", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("brand_id", sa.String(128), nullable=True),
        sa.Column("project_id", sa.String(128), nullable=True),
        sa.Column("analytics_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("campaign_key", name="uq_campaigns_campaign_key"),
    )
    op.create_index("ix_campaigns_status", "campaigns", ["status"])
    op.create_index("ix_campaigns_brand_id", "campaigns", ["brand_id"])

    op.create_table(
        "campaign_channels",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_key", sa.String(128), nullable=False),
        sa.Column("channel", sa.String(64), nullable=False),
        sa.Column("budget_share", sa.Float(), nullable=False, server_default="0"),
        sa.Column("settings_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("campaign_key", "channel", name="uq_campaign_channels_campaign_channel"),
    )
    op.create_index("ix_campaign_channels_campaign_key", "campaign_channels", ["campaign_key"])

    op.create_table(
        "media_library",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("media_key", sa.String(128), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("modality", sa.String(64), nullable=False, server_default="image"),
        sa.Column("url", sa.String(512), nullable=False, server_default=""),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("tags_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("embedding_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("media_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("media_key", name="uq_media_library_media_key"),
    )
    op.create_index("ix_media_library_modality", "media_library", ["modality"])

    op.create_table(
        "brand_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("brand_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("logos_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("colors_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("typography_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("tone_of_voice", sa.String(256), nullable=False, server_default="professional"),
        sa.Column("templates_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("assets_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
        sa.UniqueConstraint("brand_key", name="uq_brand_profiles_brand_key"),
    )

    op.create_table(
        "creative_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("history_key", sa.String(128), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=False),
        sa.Column("details_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        *_ts_cols(),
    )
    op.create_index("ix_creative_history_entity", "creative_history", ["entity_type", "entity_id"])
    op.create_index("ix_creative_history_action", "creative_history", ["action"])


def downgrade() -> None:
    op.drop_table("creative_history")
    op.drop_table("brand_profiles")
    op.drop_table("media_library")
    op.drop_table("campaign_channels")
    op.drop_table("campaigns")
    op.drop_table("creative_templates")
    op.drop_table("creative_assets")
    op.drop_table("creative_projects")
