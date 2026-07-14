"""revenue_engine_v1

Revision ID: f2c345678901
Revises: f1b234567890
Create Date: 2026-07-14 14:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f2c345678901"
down_revision: Union[str, None] = "f1b234567890"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "revenue_engine_v1_entries",
        sa.Column("deal_id", sa.UUID(), nullable=False),
        sa.Column("gross_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("platform_income", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("partner_income", sa.Numeric(precision=18, scale=2), nullable=False, server_default="0"),
        sa.Column("manager_income", sa.Numeric(precision=18, scale=2), nullable=False, server_default="0"),
        sa.Column("referral_income", sa.Numeric(precision=18, scale=2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("payment_status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["deal_id"], ["deal_engine_v1_deals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deal_id", name="uq_revenue_engine_v1_deal"),
    )
    op.create_index("ix_revenue_engine_v1_deal", "revenue_engine_v1_entries", ["deal_id"])
    op.create_index("ix_revenue_engine_v1_payment_status", "revenue_engine_v1_entries", ["payment_status"])
    op.create_index("ix_revenue_engine_v1_created", "revenue_engine_v1_entries", ["created_at"])
    op.create_index("ix_revenue_engine_v1_currency", "revenue_engine_v1_entries", ["currency"])


def downgrade() -> None:
    op.drop_index("ix_revenue_engine_v1_currency", table_name="revenue_engine_v1_entries")
    op.drop_index("ix_revenue_engine_v1_created", table_name="revenue_engine_v1_entries")
    op.drop_index("ix_revenue_engine_v1_payment_status", table_name="revenue_engine_v1_entries")
    op.drop_index("ix_revenue_engine_v1_deal", table_name="revenue_engine_v1_entries")
    op.drop_table("revenue_engine_v1_entries")
