"""Lawyer 3.4 — watch/change enrichment (additive).

Revision ID: h7c890123456
Revises: f5z678901234
Create Date: 2026-08-12 18:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "h7c890123456"
down_revision: Union[str, None] = "f5z678901234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _cols(conn, table: str) -> set[str]:
    # table names are literals from this migration only
    rows = conn.exec_driver_sql(
        f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"
    ).fetchall()
    return {r[0] for r in rows}


def upgrade() -> None:
    conn = op.get_bind()
    if conn.exec_driver_sql("SELECT to_regclass('public.legal_ops_watchlist')").scalar():
        cols = _cols(conn, "legal_ops_watchlist")
        for name, col in (
            ("title", sa.Column("title", sa.String(512), nullable=True)),
            ("source_url", sa.Column("source_url", sa.Text(), nullable=True)),
            ("check_frequency", sa.Column("check_frequency", sa.String(64), nullable=True)),
            ("comment", sa.Column("comment", sa.Text(), nullable=True)),
            ("counterparty", sa.Column("counterparty", sa.String(512), nullable=True)),
            ("decision_ref", sa.Column("decision_ref", sa.String(512), nullable=True)),
            ("enforcement_id", sa.Column("enforcement_id", sa.String(64), nullable=True)),
            ("active", sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False)),
        ):
            if name not in cols:
                op.add_column("legal_ops_watchlist", col)

    if conn.exec_driver_sql("SELECT to_regclass('public.legal_ops_monitor_changes')").scalar():
        cols = _cols(conn, "legal_ops_monitor_changes")
        for name, col in (
            ("workflow_status", sa.Column("workflow_status", sa.String(32), server_default="new", nullable=False)),
            ("summary", sa.Column("summary", sa.Text(), nullable=True)),
            ("old_fingerprint", sa.Column("old_fingerprint", sa.String(128), nullable=True)),
            ("new_fingerprint", sa.Column("new_fingerprint", sa.String(128), nullable=True)),
            ("source_reference", sa.Column("source_reference", sa.Text(), nullable=True)),
            ("enforcement_id", sa.Column("enforcement_id", sa.String(64), nullable=True)),
            ("suggestions", sa.Column("suggestions", JSONB(), nullable=True)),
        ):
            if name not in cols:
                op.add_column("legal_ops_monitor_changes", col)


def downgrade() -> None:
    pass
