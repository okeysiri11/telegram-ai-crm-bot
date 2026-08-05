"""VersionMixin full backfill — Sprint 37.1 Production Database Stabilization.

Revision ID: u4o567890123
Revises: t3n456789012
Create Date: 2026-08-04 16:25:00.000000

Idempotently adds VersionMixin columns via PostgreSQL IF NOT EXISTS.
Safe to re-run. Does not drop data. Does not change API contracts.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "u4o567890123"
down_revision: Union[str, None] = "t3n456789012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PRIORITY_TABLES: tuple[str, ...] = (
    "audit_log",
    "audit_events",
    "audit_engine_logs",
    "trust_security_engine_v1_permission_audits",
)

# (name, DDL fragment)
VERSION_COLUMNS_DDL: tuple[tuple[str, str], ...] = (
    ("version", "INTEGER NOT NULL DEFAULT 1"),
    ("change_id", "VARCHAR(64)"),
    ("source_client", "VARCHAR(32)"),
    ("workspace_id", "VARCHAR(128)"),
    ("created_by", "VARCHAR(128)"),
    ("updated_by", "VARCHAR(128)"),
    ("metadata_json", "JSONB"),
)


def _orm_version_tables() -> list[str]:
    try:
        from database.migration_models import load_all_models
        from database.base import Base

        load_all_models()
        names = [name for name, table in Base.metadata.tables.items() if "version" in table.c]
        priority = [t for t in PRIORITY_TABLES if t in names]
        rest = sorted(t for t in names if t not in priority)
        return priority + rest
    except Exception:
        return list(PRIORITY_TABLES)


def _backfill_table(table: str) -> None:
    bind = op.get_bind()
    # Skip missing tables
    exists = bind.execute(
        text("SELECT to_regclass(:t) IS NOT NULL"),
        {"t": table},
    ).scalar()
    if not exists:
        return
    for col, ddl in VERSION_COLUMNS_DDL:
        bind.execute(text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "{col}" {ddl}'))
    # Best-effort indexes (ignore failures without aborting — IF NOT EXISTS)
    bind.execute(text(f'CREATE INDEX IF NOT EXISTS "ix_{table}_change_id" ON "{table}" (change_id)'))
    bind.execute(text(f'CREATE INDEX IF NOT EXISTS "ix_{table}_workspace_id" ON "{table}" (workspace_id)'))


def upgrade() -> None:
    for table in _orm_version_tables():
        _backfill_table(table)


def downgrade() -> None:
    # Non-destructive: do not drop VersionMixin columns from production tables.
    pass
