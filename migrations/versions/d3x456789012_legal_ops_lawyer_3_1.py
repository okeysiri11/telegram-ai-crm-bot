"""Lawyer 3.1 — CRM card fields (additive, backup-safe).

Revision ID: d3x456789012
Revises: c2w345678901
Create Date: 2026-08-12 16:30:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "d3x456789012"
down_revision: Union[str, None] = "c2w345678901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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

    # Clients — cardoteka
    _add(conn, "legal_ops_clients", "client_type", sa.Column("client_type", sa.String(32), nullable=True))
    _add(conn, "legal_ops_clients", "avatar_file_id", sa.Column("avatar_file_id", sa.String(64), nullable=True))
    _add(conn, "legal_ops_clients", "address", sa.Column("address", sa.Text(), nullable=True))
    _add(conn, "legal_ops_clients", "city", sa.Column("city", sa.String(128), nullable=True))
    _add(conn, "legal_ops_clients", "country", sa.Column("country", sa.String(128), nullable=True))
    _add(conn, "legal_ops_clients", "company", sa.Column("company", sa.String(256), nullable=True))
    _add(conn, "legal_ops_clients", "position", sa.Column("position", sa.String(256), nullable=True))
    _add(conn, "legal_ops_clients", "responsible", sa.Column("responsible", sa.String(256), nullable=True))
    _add(conn, "legal_ops_clients", "source", sa.Column("source", sa.String(128), nullable=True))
    _add(conn, "legal_ops_clients", "identity_data", sa.Column("identity_data", sa.String(256), nullable=True))
    _add(conn, "legal_ops_clients", "tags", sa.Column("tags", JSONB(), nullable=True))
    _add(conn, "legal_ops_clients", "contacts", sa.Column("contacts", JSONB(), nullable=True))

    # Cases
    _add(conn, "legal_ops_cases", "court_case_number", sa.Column("court_case_number", sa.String(128), nullable=True))
    _add(conn, "legal_ops_cases", "description", sa.Column("description", sa.Text(), nullable=True))
    _add(conn, "legal_ops_cases", "deadline_at", sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True))

    # Contracts
    _add(conn, "legal_ops_contracts", "contract_type", sa.Column("contract_type", sa.String(64), nullable=True))
    _add(conn, "legal_ops_contracts", "amount", sa.Column("amount", sa.Numeric(18, 2), nullable=True))
    _add(conn, "legal_ops_contracts", "currency", sa.Column("currency", sa.String(16), nullable=True))
    _add(conn, "legal_ops_contracts", "contract_date", sa.Column("contract_date", sa.DateTime(timezone=True), nullable=True))

    # Documents
    _add(conn, "legal_ops_documents", "description", sa.Column("description", sa.Text(), nullable=True))
    _add(conn, "legal_ops_documents", "document_date", sa.Column("document_date", sa.DateTime(timezone=True), nullable=True))
    _add(conn, "legal_ops_documents", "uploaded_by", sa.Column("uploaded_by", sa.String(128), nullable=True))
    _add(conn, "legal_ops_documents", "tags", sa.Column("tags", JSONB(), nullable=True))

    # Tasks
    _add(conn, "legal_ops_tasks", "description", sa.Column("description", sa.Text(), nullable=True))
    _add(conn, "legal_ops_tasks", "client_id", sa.Column("client_id", sa.String(64), nullable=True))
    _add(conn, "legal_ops_tasks", "contract_id", sa.Column("contract_id", sa.String(64), nullable=True))
    _add(conn, "legal_ops_tasks", "priority", sa.Column("priority", sa.String(32), nullable=True))
    _add(conn, "legal_ops_tasks", "reminder_minutes", sa.Column("reminder_minutes", sa.Integer(), nullable=True))
    _add(conn, "legal_ops_tasks", "completed_at", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))

    # Hearings
    _add(conn, "legal_ops_hearings", "court_case_number", sa.Column("court_case_number", sa.String(128), nullable=True))
    _add(conn, "legal_ops_hearings", "judge", sa.Column("judge", sa.String(256), nullable=True))
    _add(conn, "legal_ops_hearings", "room", sa.Column("room", sa.String(128), nullable=True))
    _add(conn, "legal_ops_hearings", "hearing_format", sa.Column("hearing_format", sa.String(32), nullable=True))
    _add(conn, "legal_ops_hearings", "video_url", sa.Column("video_url", sa.String(1024), nullable=True))
    _add(conn, "legal_ops_hearings", "description", sa.Column("description", sa.Text(), nullable=True))
    _add(conn, "legal_ops_hearings", "result", sa.Column("result", sa.Text(), nullable=True))
    _add(conn, "legal_ops_hearings", "notes", sa.Column("notes", sa.Text(), nullable=True))
    _add(conn, "legal_ops_hearings", "ends_at", sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Additive migration — keep columns to protect production data.
    pass
