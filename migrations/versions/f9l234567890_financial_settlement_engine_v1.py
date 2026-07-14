"""financial_settlement_engine_v1

Revision ID: f9l234567890
Revises: f9k123456789
Create Date: 2026-07-14 17:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f9l234567890"
down_revision: Union[str, None] = "f9k123456789"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE payment_engine_v1_payments "
            "SET status = 'SCREENSHOT_UPLOADED' WHERE status = 'PAYMENT_UPLOADED'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE payment_engine_v1_payments "
            "SET status = 'UNDER_VERIFICATION' WHERE status = 'UNDER_REVIEW'"
        )
    )

    op.create_table(
        "financial_settlement_v1_revenues",
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("deal_id", sa.UUID(), nullable=False),
        sa.Column("revenue_entry_id", sa.UUID(), nullable=True),
        sa.Column("gross_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("platform_profit", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["deal_id"], ["deal_engine_v1_deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["payment_id"], ["payment_engine_v1_payments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["revenue_entry_id"],
            ["revenue_engine_v1_entries.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_id", name="uq_fin_settlement_v1_revenue_payment"),
    )
    op.create_index(
        "ix_fin_settlement_v1_revenue_deal",
        "financial_settlement_v1_revenues",
        ["deal_id"],
    )
    op.create_index(
        "ix_fin_settlement_v1_revenue_created",
        "financial_settlement_v1_revenues",
        ["created_at"],
    )

    op.create_table(
        "financial_settlement_v1_settlements",
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("deal_id", sa.UUID(), nullable=False),
        sa.Column("revenue_id", sa.UUID(), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=True),
        sa.Column("manager_id", sa.UUID(), nullable=True),
        sa.Column("client_payment", sa.Numeric(18, 2), nullable=False),
        sa.Column("partner_share", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("manager_share", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("platform_profit", sa.Numeric(18, 2), nullable=False),
        sa.Column("referral_share", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
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
        sa.ForeignKeyConstraint(["deal_id"], ["deal_engine_v1_deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["partner_id"], ["automotive_partner_v1_partners.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["payment_id"], ["payment_engine_v1_payments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["revenue_id"],
            ["financial_settlement_v1_revenues.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_id", name="uq_fin_settlement_v1_settlement_payment"),
    )
    op.create_index(
        "ix_fin_settlement_v1_settlement_deal",
        "financial_settlement_v1_settlements",
        ["deal_id"],
    )
    op.create_index(
        "ix_fin_settlement_v1_settlement_status",
        "financial_settlement_v1_settlements",
        ["status"],
    )
    op.create_index(
        "ix_fin_settlement_v1_settlement_created",
        "financial_settlement_v1_settlements",
        ["created_at"],
    )

    op.create_table(
        "financial_settlement_v1_commissions",
        sa.Column("settlement_id", sa.UUID(), nullable=False),
        sa.Column("recipient_type", sa.String(length=50), nullable=False),
        sa.Column("recipient_id", sa.UUID(), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACCRUED"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["settlement_id"],
            ["financial_settlement_v1_settlements.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fin_settlement_v1_comm_settlement",
        "financial_settlement_v1_commissions",
        ["settlement_id"],
    )
    op.create_index(
        "ix_fin_settlement_v1_comm_recipient",
        "financial_settlement_v1_commissions",
        ["recipient_type", "recipient_id"],
    )
    op.create_index(
        "ix_fin_settlement_v1_comm_status",
        "financial_settlement_v1_commissions",
        ["status"],
    )

    op.create_table(
        "financial_settlement_v1_treasury_transactions",
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("settlement_id", sa.UUID(), nullable=False),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["payment_id"], ["payment_engine_v1_payments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["settlement_id"],
            ["financial_settlement_v1_settlements.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fin_settlement_v1_treasury_payment",
        "financial_settlement_v1_treasury_transactions",
        ["payment_id"],
    )
    op.create_index(
        "ix_fin_settlement_v1_treasury_settlement",
        "financial_settlement_v1_treasury_transactions",
        ["settlement_id"],
    )
    op.create_index(
        "ix_fin_settlement_v1_treasury_type",
        "financial_settlement_v1_treasury_transactions",
        ["transaction_type"],
    )
    op.create_index(
        "ix_fin_settlement_v1_treasury_created",
        "financial_settlement_v1_treasury_transactions",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_fin_settlement_v1_treasury_created", table_name="financial_settlement_v1_treasury_transactions")
    op.drop_index("ix_fin_settlement_v1_treasury_type", table_name="financial_settlement_v1_treasury_transactions")
    op.drop_index("ix_fin_settlement_v1_treasury_settlement", table_name="financial_settlement_v1_treasury_transactions")
    op.drop_index("ix_fin_settlement_v1_treasury_payment", table_name="financial_settlement_v1_treasury_transactions")
    op.drop_table("financial_settlement_v1_treasury_transactions")

    op.drop_index("ix_fin_settlement_v1_comm_status", table_name="financial_settlement_v1_commissions")
    op.drop_index("ix_fin_settlement_v1_comm_recipient", table_name="financial_settlement_v1_commissions")
    op.drop_index("ix_fin_settlement_v1_comm_settlement", table_name="financial_settlement_v1_commissions")
    op.drop_table("financial_settlement_v1_commissions")

    op.drop_index("ix_fin_settlement_v1_settlement_created", table_name="financial_settlement_v1_settlements")
    op.drop_index("ix_fin_settlement_v1_settlement_status", table_name="financial_settlement_v1_settlements")
    op.drop_index("ix_fin_settlement_v1_settlement_deal", table_name="financial_settlement_v1_settlements")
    op.drop_table("financial_settlement_v1_settlements")

    op.drop_index("ix_fin_settlement_v1_revenue_created", table_name="financial_settlement_v1_revenues")
    op.drop_index("ix_fin_settlement_v1_revenue_deal", table_name="financial_settlement_v1_revenues")
    op.drop_table("financial_settlement_v1_revenues")

    op.execute(
        sa.text(
            "UPDATE payment_engine_v1_payments "
            "SET status = 'PAYMENT_UPLOADED' WHERE status = 'SCREENSHOT_UPLOADED'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE payment_engine_v1_payments "
            "SET status = 'UNDER_REVIEW' WHERE status = 'UNDER_VERIFICATION'"
        )
    )
