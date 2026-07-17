"""Platform audit_events table.

Revision ID: f9y567890123
Revises: f9x456789012
Create Date: 2026-07-17 14:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "f9y567890123"
down_revision: Union[str, None] = "f9x456789012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=True),
        sa.Column("old_value", JSONB(), nullable=True),
        sa.Column("new_value", JSONB(), nullable=True),
        sa.Column("metadata_json", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])
    op.create_index("ix_audit_events_entity", "audit_events", ["entity_type", "entity_id"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_actor_id", "audit_events", ["actor_id"])
    op.create_index(
        "ix_audit_events_metadata_manager_id",
        "audit_events",
        ["metadata_json"],
        postgresql_using="gin",
        postgresql_ops={"metadata_json": "jsonb_path_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_audit_events_metadata_manager_id", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_id", table_name="audit_events")
    op.drop_index("ix_audit_events_event_type", table_name="audit_events")
    op.drop_index("ix_audit_events_entity", table_name="audit_events")
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_table("audit_events")
