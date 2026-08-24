"""Lawyer Desk 51.1 — archive, files, calendar fields (additive).

Revision ID: c2w345678901
Revises: b1v234567890
Create Date: 2026-08-12 14:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "c2w345678901"
down_revision: Union[str, None] = "b1v234567890"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENTITY_TABLES = [
    "legal_ops_clients",
    "legal_ops_cases",
    "legal_ops_contracts",
    "legal_ops_documents",
    "legal_ops_tasks",
    "legal_ops_hearings",
    "legal_ops_calendar_events",
]


def _has_column(conn, table: str, column: str) -> bool:
    row = conn.exec_driver_sql(
        "SELECT 1 FROM information_schema.columns "
        f"WHERE table_name = '{table}' AND column_name = '{column}'"
    ).scalar()
    return row is not None


def _exists(conn, name: str) -> bool:
    return conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar() is not None


def _add(conn, table: str, column: str, col: sa.Column) -> None:
    if _exists(conn, table) and not _has_column(conn, table, column):
        op.add_column(table, col)


def upgrade() -> None:
    conn = op.get_bind()
    for table in ENTITY_TABLES:
        _add(conn, table, "archived_at", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
        _add(conn, table, "archived_by", sa.Column("archived_by", sa.String(128), nullable=True))
        _add(conn, table, "archive_reason", sa.Column("archive_reason", sa.Text(), nullable=True))

    _add(conn, "legal_ops_cases", "case_type", sa.Column("case_type", sa.String(64), nullable=True))
    _add(conn, "legal_ops_cases", "court", sa.Column("court", sa.String(256), nullable=True))
    _add(conn, "legal_ops_cases", "judge", sa.Column("judge", sa.String(256), nullable=True))
    _add(conn, "legal_ops_cases", "notes", sa.Column("notes", sa.Text(), nullable=True))
    _add(conn, "legal_ops_cases", "priority", sa.Column("priority", sa.String(32), nullable=True))
    _add(conn, "legal_ops_cases", "participants", sa.Column("participants", JSONB(), nullable=True))
    _add(conn, "legal_ops_cases", "opened_at", sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True))
    _add(conn, "legal_ops_cases", "closed_at", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))

    _add(conn, "legal_ops_contracts", "contract_number", sa.Column("contract_number", sa.String(128), nullable=True))
    _add(conn, "legal_ops_contracts", "counterparty", sa.Column("counterparty", sa.String(256), nullable=True))
    _add(conn, "legal_ops_contracts", "responsible", sa.Column("responsible", sa.String(256), nullable=True))
    _add(conn, "legal_ops_contracts", "start_at", sa.Column("start_at", sa.DateTime(timezone=True), nullable=True))
    _add(conn, "legal_ops_contracts", "end_at", sa.Column("end_at", sa.DateTime(timezone=True), nullable=True))
    _add(conn, "legal_ops_contracts", "deadline_at", sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True))
    _add(conn, "legal_ops_contracts", "notes", sa.Column("notes", sa.Text(), nullable=True))
    _add(conn, "legal_ops_contracts", "signing_status", sa.Column("signing_status", sa.String(64), nullable=True))

    _add(conn, "legal_ops_calendar_events", "event_type", sa.Column("event_type", sa.String(64), nullable=True))
    _add(conn, "legal_ops_calendar_events", "all_day", sa.Column("all_day", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    _add(conn, "legal_ops_calendar_events", "client_id", sa.Column("client_id", sa.String(64), nullable=True))
    _add(conn, "legal_ops_calendar_events", "contract_id", sa.Column("contract_id", sa.String(64), nullable=True))
    _add(conn, "legal_ops_calendar_events", "task_id", sa.Column("task_id", sa.String(64), nullable=True))
    _add(conn, "legal_ops_calendar_events", "responsible_user_id", sa.Column("responsible_user_id", sa.String(128), nullable=True))
    _add(conn, "legal_ops_calendar_events", "location", sa.Column("location", sa.String(512), nullable=True))
    _add(conn, "legal_ops_calendar_events", "description", sa.Column("description", sa.Text(), nullable=True))
    _add(conn, "legal_ops_calendar_events", "reminder_minutes", sa.Column("reminder_minutes", sa.Integer(), nullable=True))
    _add(conn, "legal_ops_calendar_events", "source_kind", sa.Column("source_kind", sa.String(64), nullable=True))
    _add(conn, "legal_ops_calendar_events", "source_id", sa.Column("source_id", sa.String(64), nullable=True))
    _add(conn, "legal_ops_calendar_events", "external_event_id", sa.Column("external_event_id", sa.String(256), nullable=True))
    _add(conn, "legal_ops_calendar_events", "external_provider", sa.Column("external_provider", sa.String(64), nullable=True))

    if not _exists(conn, "legal_ops_files"):
        op.create_table(
            "legal_ops_files",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("entity_type", sa.String(64), nullable=True),
            sa.Column("entity_id", sa.String(64), nullable=True),
            sa.Column("filename", sa.String(512), nullable=False),
            sa.Column("mime_type", sa.String(128), nullable=True),
            sa.Column("size", sa.Integer(), nullable=True),
            sa.Column("storage_path", sa.String(1024), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("file_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("uploaded_by", sa.String(128), nullable=True),
            sa.Column("inbox_status", sa.String(32), nullable=False, server_default="linked"),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("archived_by", sa.String(128), nullable=True),
            sa.Column("archive_reason", sa.Text(), nullable=True),
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
        op.create_index("ix_legal_ops_files_org", "legal_ops_files", ["organization_id"])
        op.create_index("ix_legal_ops_files_entity", "legal_ops_files", ["entity_type", "entity_id"])
        op.create_index("ix_legal_ops_files_inbox", "legal_ops_files", ["inbox_status"])


def downgrade() -> None:
    pass
