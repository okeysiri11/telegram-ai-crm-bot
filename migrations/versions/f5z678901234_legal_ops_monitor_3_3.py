"""Lawyer 3.3 — monitoring / enforcement / calendar mapping (additive).

Revision ID: f5z678901234
Revises: e4y567890123
Create Date: 2026-08-12 17:30:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "f5z678901234"
down_revision: Union[str, None] = "e4y567890123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _exists(conn, name: str) -> bool:
    return conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()
    if not _exists(conn, "legal_ops_watchlist"):
        op.create_table(
            "legal_ops_watchlist",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("case_id", sa.String(64), nullable=True),
            sa.Column("client_id", sa.String(64), nullable=True),
            sa.Column("entity_kind", sa.String(32), nullable=False, server_default="court_case"),
            sa.Column("external_case_number", sa.String(128), nullable=True),
            sa.Column("provider", sa.String(64), nullable=False, server_default="manual_import"),
            sa.Column("status", sa.String(32), nullable=False, server_default="active"),
            sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("next_check_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("fingerprint", sa.String(128), nullable=True),
            sa.Column("normalized_state", JSONB(), nullable=True),
            sa.Column("automation", JSONB(), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("archived_by", sa.String(128), nullable=True),
            sa.Column("archive_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("version", sa.Integer(), server_default="1", nullable=False),
            sa.Column("change_id", sa.String(length=64), nullable=True),
            sa.Column("source_client", sa.String(length=32), nullable=True),
            sa.Column("workspace_id", sa.String(length=128), nullable=True),
            sa.Column("created_by", sa.String(length=128), nullable=True),
            sa.Column("updated_by", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=True),
        )
        op.create_index("ix_legal_ops_watchlist_org", "legal_ops_watchlist", ["organization_id"])
        op.create_index("ix_legal_ops_watchlist_case", "legal_ops_watchlist", ["case_id"])
        op.create_index("ix_legal_ops_watchlist_ext", "legal_ops_watchlist", ["external_case_number"])

    if not _exists(conn, "legal_ops_monitor_changes"):
        op.create_table(
            "legal_ops_monitor_changes",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("watchlist_id", sa.String(64), nullable=True),
            sa.Column("case_id", sa.String(64), nullable=True),
            sa.Column("client_id", sa.String(64), nullable=True),
            sa.Column("change_type", sa.String(64), nullable=False),
            sa.Column("title", sa.String(512), nullable=False),
            sa.Column("detail", JSONB(), nullable=True),
            sa.Column("dedupe_key", sa.String(128), nullable=False),
            sa.Column("provider", sa.String(64), nullable=True),
            sa.Column("source_label", sa.String(256), nullable=True),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("archived_by", sa.String(128), nullable=True),
            sa.Column("archive_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("version", sa.Integer(), server_default="1", nullable=False),
            sa.Column("change_id", sa.String(length=64), nullable=True),
            sa.Column("source_client", sa.String(length=32), nullable=True),
            sa.Column("workspace_id", sa.String(length=128), nullable=True),
            sa.Column("created_by", sa.String(length=128), nullable=True),
            sa.Column("updated_by", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=True),
        )
        op.create_index("ix_legal_ops_monitor_changes_org", "legal_ops_monitor_changes", ["organization_id"])
        op.create_index(
            "ix_legal_ops_monitor_changes_dedupe",
            "legal_ops_monitor_changes",
            ["organization_id", "dedupe_key"],
            unique=True,
        )

    if not _exists(conn, "legal_ops_enforcement"):
        op.create_table(
            "legal_ops_enforcement",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("production_number", sa.String(128), nullable=False),
            sa.Column("client_id", sa.String(64), nullable=True),
            sa.Column("case_id", sa.String(64), nullable=True),
            sa.Column("debtor", sa.String(512), nullable=True),
            sa.Column("creditor", sa.String(512), nullable=True),
            sa.Column("executor", sa.String(512), nullable=True),
            sa.Column("status", sa.String(64), nullable=False, server_default="open"),
            sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("provider", sa.String(64), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("archived_by", sa.String(128), nullable=True),
            sa.Column("archive_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("version", sa.Integer(), server_default="1", nullable=False),
            sa.Column("change_id", sa.String(length=64), nullable=True),
            sa.Column("source_client", sa.String(length=32), nullable=True),
            sa.Column("workspace_id", sa.String(length=128), nullable=True),
            sa.Column("created_by", sa.String(length=128), nullable=True),
            sa.Column("updated_by", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=True),
        )
        op.create_index("ix_legal_ops_enforcement_org", "legal_ops_enforcement", ["organization_id"])

    if not _exists(conn, "legal_ops_calendar_mappings"):
        op.create_table(
            "legal_ops_calendar_mappings",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("internal_event_id", sa.String(64), nullable=False),
            sa.Column("provider", sa.String(64), nullable=False, server_default="google"),
            sa.Column("external_calendar_id", sa.String(256), nullable=True),
            sa.Column("external_event_id", sa.String(256), nullable=False),
            sa.Column("sync_version", sa.Integer(), server_default="1", nullable=False),
            sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sync_direction", sa.String(32), nullable=False, server_default="ados_to_google"),
            sa.Column("payload", JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("version", sa.Integer(), server_default="1", nullable=False),
            sa.Column("change_id", sa.String(length=64), nullable=True),
            sa.Column("source_client", sa.String(length=32), nullable=True),
            sa.Column("workspace_id", sa.String(length=128), nullable=True),
            sa.Column("created_by", sa.String(length=128), nullable=True),
            sa.Column("updated_by", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=True),
        )
        op.create_index(
            "ix_legal_ops_cal_map_internal",
            "legal_ops_calendar_mappings",
            ["organization_id", "internal_event_id", "provider"],
            unique=True,
        )
        op.create_index(
            "ix_legal_ops_cal_map_external",
            "legal_ops_calendar_mappings",
            ["organization_id", "external_event_id"],
        )

    if not _exists(conn, "legal_ops_monitor_settings"):
        op.create_table(
            "legal_ops_monitor_settings",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, unique=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("timezone", sa.String(64), nullable=False, server_default="Europe/Kyiv"),
            sa.Column("cron_morning", sa.String(64), nullable=False, server_default="0 9 * * *"),
            sa.Column("cron_evening", sa.String(64), nullable=False, server_default="0 18 * * *"),
            sa.Column("google_sync", JSONB(), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("version", sa.Integer(), server_default="1", nullable=False),
            sa.Column("change_id", sa.String(length=64), nullable=True),
            sa.Column("source_client", sa.String(length=32), nullable=True),
            sa.Column("workspace_id", sa.String(length=128), nullable=True),
            sa.Column("created_by", sa.String(length=128), nullable=True),
            sa.Column("updated_by", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=True),
        )


def downgrade() -> None:
    pass
