"""Platform request_sla table.

Revision ID: f9a789012345
Revises: f9z678901234
Create Date: 2026-07-18 10:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "f9a789012345"
down_revision: Union[str, None] = "f9z678901234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "request_sla",
        sa.Column("request_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("manager_id", sa.BigInteger(), nullable=True),
        sa.Column("first_response_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completion_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("escalation_level", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("first_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_request_sla_manager_id", "request_sla", ["manager_id"])
    op.create_index("ix_request_sla_first_response_deadline", "request_sla", ["first_response_deadline"])
    op.create_index("ix_request_sla_escalation_level", "request_sla", ["escalation_level"])
    op.create_index("ix_request_sla_first_response_at", "request_sla", ["first_response_at"])
    op.create_index("ix_request_sla_completed_at", "request_sla", ["completed_at"])


def downgrade() -> None:
    op.drop_index("ix_request_sla_completed_at", table_name="request_sla")
    op.drop_index("ix_request_sla_first_response_at", table_name="request_sla")
    op.drop_index("ix_request_sla_escalation_level", table_name="request_sla")
    op.drop_index("ix_request_sla_first_response_deadline", table_name="request_sla")
    op.drop_index("ix_request_sla_manager_id", table_name="request_sla")
    op.drop_table("request_sla")
