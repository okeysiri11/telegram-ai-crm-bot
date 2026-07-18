"""Platform owner escalation revision.

Revision ID: f9b890123456
Revises: f9a789012345
Create Date: 2026-07-18 11:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f9b890123456"
down_revision: Union[str, None] = "f9a789012345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "request_sla",
        sa.Column("owner_escalated", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "request_sla",
        sa.Column("owner_escalated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "request_sla",
        sa.Column("owner_notification_sent", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index("ix_request_sla_owner_escalated", "request_sla", ["owner_escalated"])


def downgrade() -> None:
    op.drop_index("ix_request_sla_owner_escalated", table_name="request_sla")
    op.drop_column("request_sla", "owner_notification_sent")
    op.drop_column("request_sla", "owner_escalated_at")
    op.drop_column("request_sla", "owner_escalated")
