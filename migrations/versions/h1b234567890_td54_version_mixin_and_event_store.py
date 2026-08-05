"""TD-54 VersionMixin retrofit + optional platform_events table — Sprint 35.1.

Revision ID: h1b234567890
Revises: g0a123456789
Create Date: 2026-08-03 09:40:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import inspect

revision: str = "h1b234567890"
down_revision: Union[str, None] = "g0a123456789"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Core + high-traffic entity tables (full ORM coverage is in models; migration seeds DB columns).
CORE_TABLES: tuple[str, ...] = (
    "users",
    "tasks",
    "calendar_events",
    "deals",
    "lead_engine_v1_leads",
    "client_requests",
    "notifications",
    "car_engine_v1_cars",
    "partners",
    "workflow_executions",
)

VERSION_COLUMNS = (
    ("version", sa.Column("version", sa.Integer(), server_default="1", nullable=False)),
    ("change_id", sa.Column("change_id", sa.String(length=64), nullable=True)),
    ("source_client", sa.Column("source_client", sa.String(length=32), nullable=True)),
    ("workspace_id", sa.Column("workspace_id", sa.String(length=128), nullable=True)),
    ("created_by", sa.Column("created_by", sa.String(length=128), nullable=True)),
    ("updated_by", sa.Column("updated_by", sa.String(length=128), nullable=True)),
    ("metadata_json", sa.Column("metadata_json", JSONB(), nullable=True)),
)


def _existing_columns(table: str) -> set[str]:
    bind = op.get_bind()
    insp = inspect(bind)
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    for table in CORE_TABLES:
        existing = _existing_columns(table)
        if not existing:
            continue
        for name, col in VERSION_COLUMNS:
            if name in existing:
                continue
            op.add_column(table, col)
        if "change_id" not in existing:
            try:
                op.create_index(f"ix_{table}_change_id", table, ["change_id"])
            except Exception:
                pass
        if "workspace_id" not in existing:
            try:
                op.create_index(f"ix_{table}_workspace_id", table, ["workspace_id"])
            except Exception:
                pass

    # Optional Postgres Event Store table (ADOS_EVENT_STORE_BACKEND=postgres)
    existing = _existing_columns("platform_state_events")
    if not existing:
        op.create_table(
            "platform_state_events",
            sa.Column("seq", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("event_id", sa.String(length=64), nullable=False, unique=True),
            sa.Column("event_type", sa.String(length=128), nullable=False),
            sa.Column("entity_type", sa.String(length=128), nullable=False),
            sa.Column("entity_id", sa.String(length=128), nullable=False),
            sa.Column("workspace_id", sa.String(length=128), nullable=True),
            sa.Column("tenant_id", sa.String(length=128), nullable=True),
            sa.Column("change_id", sa.String(length=64), nullable=True),
            sa.Column("version", sa.Integer(), server_default="1", nullable=False),
            sa.Column("actor_id", sa.String(length=128), nullable=True),
            sa.Column("source_client", sa.String(length=32), nullable=True),
            sa.Column("agent_id", sa.String(length=128), nullable=True),
            sa.Column("payload_json", JSONB(), nullable=False),
            sa.Column("before_json", JSONB(), nullable=True),
            sa.Column("after_json", JSONB(), nullable=True),
            sa.Column("occurred_at", sa.String(length=64), nullable=False),
            sa.Column("stream_key", sa.String(length=256), nullable=False),
        )
        op.create_index("ix_platform_state_events_stream", "platform_state_events", ["stream_key", "seq"])
        op.create_index("ix_platform_state_events_workspace", "platform_state_events", ["workspace_id", "seq"])
        op.create_index("ix_platform_state_events_type", "platform_state_events", ["event_type", "seq"])


def downgrade() -> None:
    op.drop_table("platform_state_events")
    for table in reversed(CORE_TABLES):
        existing = _existing_columns(table)
        if not existing:
            continue
        for name, _ in reversed(VERSION_COLUMNS):
            if name in existing:
                op.drop_column(table, name)
