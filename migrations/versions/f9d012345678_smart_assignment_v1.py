"""Smart assignment engine — assignment_scores + manager_pool specialization.

Revision ID: f9d012345678
Revises: f9c901234567
Create Date: 2026-07-18 14:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "f9d012345678"
down_revision: Union[str, None] = "f9c901234567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "manager_pool",
        sa.Column("specialization", sa.String(length=32), server_default="MULTI", nullable=False),
    )
    op.create_index("ix_manager_pool_specialization", "manager_pool", ["specialization"])

    op.create_table(
        "assignment_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", UUID(as_uuid=True), nullable=True),
        sa.Column("request_number", sa.String(length=32), nullable=True),
        sa.Column("manager_pool_id", UUID(as_uuid=True), nullable=False),
        sa.Column("manager_user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("manager_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("segment", sa.String(length=32), nullable=False),
        sa.Column("specialization", sa.String(length=32), nullable=True),
        sa.Column("score", sa.Float(), server_default="0", nullable=False),
        sa.Column("strategy", sa.String(length=32), server_default="SMART", nullable=False),
        sa.Column("assignment_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("response_time_seconds", sa.Integer(), nullable=True),
        sa.Column("resolution_time_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_assignment_scores_segment", "assignment_scores", ["segment"])
    op.create_index("ix_assignment_scores_strategy", "assignment_scores", ["strategy"])
    op.create_index("ix_assignment_scores_manager_pool_id", "assignment_scores", ["manager_pool_id"])
    op.create_index("ix_assignment_scores_request_id", "assignment_scores", ["request_id"])
    op.create_index("ix_assignment_scores_assignment_time", "assignment_scores", ["assignment_time"])
    op.create_index("ix_assignment_scores_completed", "assignment_scores", ["completed"])


def downgrade() -> None:
    op.drop_index("ix_assignment_scores_completed", table_name="assignment_scores")
    op.drop_index("ix_assignment_scores_assignment_time", table_name="assignment_scores")
    op.drop_index("ix_assignment_scores_request_id", table_name="assignment_scores")
    op.drop_index("ix_assignment_scores_manager_pool_id", table_name="assignment_scores")
    op.drop_index("ix_assignment_scores_strategy", table_name="assignment_scores")
    op.drop_index("ix_assignment_scores_segment", table_name="assignment_scores")
    op.drop_table("assignment_scores")
    op.drop_index("ix_manager_pool_specialization", table_name="manager_pool")
    op.drop_column("manager_pool", "specialization")
