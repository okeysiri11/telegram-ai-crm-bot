"""payment_engine_v1

Revision ID: f9j012345678
Revises: f8i901234567
Create Date: 2026-07-14 15:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f9j012345678"
down_revision: Union[str, None] = "f8i901234567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_engine_v1_payments",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("deal_id", sa.UUID(), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("payment_method", sa.String(length=50), nullable=False),
        sa.Column("payment_reference", sa.String(length=255), nullable=True),
        sa.Column("screenshot_file_id", sa.String(length=255), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="CREATED"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["client_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["deal_id"], ["deal_engine_v1_deals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["cart_engine_v1_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_engine_v1_order", "payment_engine_v1_payments", ["order_id"])
    op.create_index("ix_payment_engine_v1_client", "payment_engine_v1_payments", ["client_id"])
    op.create_index("ix_payment_engine_v1_status", "payment_engine_v1_payments", ["status"])
    op.create_index("ix_payment_engine_v1_method", "payment_engine_v1_payments", ["payment_method"])
    op.create_index("ix_payment_engine_v1_deal", "payment_engine_v1_payments", ["deal_id"])


def downgrade() -> None:
    op.drop_index("ix_payment_engine_v1_deal", table_name="payment_engine_v1_payments")
    op.drop_index("ix_payment_engine_v1_method", table_name="payment_engine_v1_payments")
    op.drop_index("ix_payment_engine_v1_status", table_name="payment_engine_v1_payments")
    op.drop_index("ix_payment_engine_v1_client", table_name="payment_engine_v1_payments")
    op.drop_index("ix_payment_engine_v1_order", table_name="payment_engine_v1_payments")
    op.drop_table("payment_engine_v1_payments")
