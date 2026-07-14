"""cart_engine_v1

Revision ID: f3d456789012
Revises: f2c345678901
Create Date: 2026-07-14 15:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f3d456789012"
down_revision: Union[str, None] = "f2c345678901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cart_engine_v1_orders",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("vertical", sa.String(length=50), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="CREATED"),
        sa.Column("payment_instructions", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cart_engine_v1_orders_user", "cart_engine_v1_orders", ["user_id"])
    op.create_index("ix_cart_engine_v1_orders_vertical", "cart_engine_v1_orders", ["vertical"])
    op.create_index("ix_cart_engine_v1_orders_status", "cart_engine_v1_orders", ["status"])
    op.create_index("ix_cart_engine_v1_orders_payment_method", "cart_engine_v1_orders", ["payment_method"])
    op.create_index("ix_cart_engine_v1_orders_created", "cart_engine_v1_orders", ["created_at"])

    op.create_table(
        "cart_engine_v1_order_items",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("service_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("line_total", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["order_id"], ["cart_engine_v1_orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", "service_code", name="uq_cart_engine_v1_item_service"),
    )
    op.create_index("ix_cart_engine_v1_items_order", "cart_engine_v1_order_items", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_cart_engine_v1_items_order", table_name="cart_engine_v1_order_items")
    op.drop_table("cart_engine_v1_order_items")
    op.drop_index("ix_cart_engine_v1_orders_created", table_name="cart_engine_v1_orders")
    op.drop_index("ix_cart_engine_v1_orders_payment_method", table_name="cart_engine_v1_orders")
    op.drop_index("ix_cart_engine_v1_orders_status", table_name="cart_engine_v1_orders")
    op.drop_index("ix_cart_engine_v1_orders_vertical", table_name="cart_engine_v1_orders")
    op.drop_index("ix_cart_engine_v1_orders_user", table_name="cart_engine_v1_orders")
    op.drop_table("cart_engine_v1_orders")
