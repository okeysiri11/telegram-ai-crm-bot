"""Lawyer Operator Desk CRM tables — Sprint 51.0 (additive).

Revision ID: b1v234567890
Revises: a0u123456789
Create Date: 2026-08-12 12:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "b1v234567890"
down_revision: Union[str, None] = "a0u123456789"
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
    conn = op.get_bind()

    def _exists(name: str) -> bool:
        return conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar() is not None

    if not _exists("legal_ops_clients"):
        op.create_table(
            "legal_ops_clients",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("email", sa.String(256), nullable=True),
            sa.Column("phone", sa.String(64), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="active"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_legal_ops_clients_org", "legal_ops_clients", ["organization_id"])
        op.create_index("ix_legal_ops_clients_tenant", "legal_ops_clients", ["tenant_id"])

    if not _exists("legal_ops_cases"):
        op.create_table(
            "legal_ops_cases",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("client_id", sa.String(64), nullable=True),
            sa.Column("title", sa.String(512), nullable=False),
            sa.Column("case_number", sa.String(128), nullable=True),
            sa.Column("status", sa.String(64), nullable=False, server_default="open"),
            sa.Column("practice_area", sa.String(128), nullable=True),
            sa.Column("responsible", sa.String(256), nullable=True),
            sa.Column("timeline", JSONB(), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_legal_ops_cases_org", "legal_ops_cases", ["organization_id"])
        op.create_index("ix_legal_ops_cases_client", "legal_ops_cases", ["client_id"])

    if not _exists("legal_ops_contracts"):
        op.create_table(
            "legal_ops_contracts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("client_id", sa.String(64), nullable=True),
            sa.Column("case_id", sa.String(64), nullable=True),
            sa.Column("title", sa.String(512), nullable=False),
            sa.Column("status", sa.String(64), nullable=False, server_default="draft"),
            sa.Column("approval_status", sa.String(64), nullable=False, server_default="pending"),
            sa.Column("body", sa.Text(), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_legal_ops_contracts_org", "legal_ops_contracts", ["organization_id"])

    if not _exists("legal_ops_documents"):
        op.create_table(
            "legal_ops_documents",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("client_id", sa.String(64), nullable=True),
            sa.Column("case_id", sa.String(64), nullable=True),
            sa.Column("contract_id", sa.String(64), nullable=True),
            sa.Column("title", sa.String(512), nullable=False),
            sa.Column("doc_type", sa.String(64), nullable=True),
            sa.Column("storage_ref", sa.String(1024), nullable=True),
            sa.Column("content_hash", sa.String(128), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="uploaded"),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_legal_ops_documents_org", "legal_ops_documents", ["organization_id"])

    if not _exists("legal_ops_tasks"):
        op.create_table(
            "legal_ops_tasks",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("case_id", sa.String(64), nullable=True),
            sa.Column("title", sa.String(512), nullable=False),
            sa.Column("kind", sa.String(64), nullable=False, server_default="task"),
            sa.Column("status", sa.String(64), nullable=False, server_default="open"),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("assignee", sa.String(256), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_legal_ops_tasks_org", "legal_ops_tasks", ["organization_id"])

    if not _exists("legal_ops_hearings"):
        op.create_table(
            "legal_ops_hearings",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("case_id", sa.String(64), nullable=True),
            sa.Column("title", sa.String(512), nullable=False),
            sa.Column("court_name", sa.String(256), nullable=True),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(64), nullable=False, server_default="scheduled"),
            sa.Column("location", sa.String(512), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_legal_ops_hearings_org", "legal_ops_hearings", ["organization_id"])

    if not _exists("legal_ops_calendar_events"):
        op.create_table(
            "legal_ops_calendar_events",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("case_id", sa.String(64), nullable=True),
            sa.Column("hearing_id", sa.String(64), nullable=True),
            sa.Column("title", sa.String(512), nullable=False),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("dedupe_key", sa.String(256), nullable=True),
            sa.Column("gcal_event_id", sa.String(256), nullable=True),
            sa.Column("sync_status", sa.String(64), nullable=False, server_default="local"),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
            sa.UniqueConstraint("organization_id", "dedupe_key", name="uq_legal_ops_cal_dedupe"),
            sa.UniqueConstraint("organization_id", "gcal_event_id", name="uq_legal_ops_cal_gcal"),
        )
        op.create_index("ix_legal_ops_cal_org", "legal_ops_calendar_events", ["organization_id"])

    if not _exists("legal_ops_activity"):
        op.create_table(
            "legal_ops_activity",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("entity_type", sa.String(64), nullable=False),
            sa.Column("entity_id", sa.String(64), nullable=False),
            sa.Column("action", sa.String(128), nullable=False),
            sa.Column("actor_role", sa.String(64), nullable=True),
            sa.Column("actor_id", sa.String(128), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("payload", JSONB(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_legal_ops_activity_org", "legal_ops_activity", ["organization_id"])
        op.create_index("ix_legal_ops_activity_entity", "legal_ops_activity", ["entity_type", "entity_id"])


def downgrade() -> None:
    # Additive sprint — do not drop production data automatically.
    pass
