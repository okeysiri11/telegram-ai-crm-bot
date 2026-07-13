"""dealer_quote_authority_v1

Revision ID: d1e2f3a45678
Revises: c0d1e2f34567
Create Date: 2026-07-13 18:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d1e2f3a45678"
down_revision: Union[str, None] = "c0d1e2f34567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dealer_quote_authority_v1_reference_quotes",
        sa.Column("source_code", sa.String(length=32), nullable=False),
        sa.Column("pair", sa.String(length=32), nullable=False),
        sa.Column("bid", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("ask", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("mid", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dqa_ref_source", "dealer_quote_authority_v1_reference_quotes", ["source_code"], unique=False)
    op.create_index("ix_dqa_ref_pair", "dealer_quote_authority_v1_reference_quotes", ["pair"], unique=False)
    op.create_index("ix_dqa_ref_captured", "dealer_quote_authority_v1_reference_quotes", ["captured_at"], unique=False)

    op.create_table(
        "dealer_quote_authority_v1_deviations",
        sa.Column("pair", sa.String(length=32), nullable=False),
        sa.Column("source_code", sa.String(length=32), nullable=False),
        sa.Column("dealer_mid", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("reference_mid", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("deviation_abs", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("deviation_pct", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dealer_sheet_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["dealer_sheet_id"],
            ["automotive_treasury_v1_rate_sheets.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dqa_dev_pair", "dealer_quote_authority_v1_deviations", ["pair"], unique=False)
    op.create_index("ix_dqa_dev_source", "dealer_quote_authority_v1_deviations", ["source_code"], unique=False)
    op.create_index("ix_dqa_dev_calculated", "dealer_quote_authority_v1_deviations", ["calculated_at"], unique=False)

    op.create_table(
        "dealer_quote_authority_v1_market_alerts",
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("pair", sa.String(length=32), nullable=False),
        sa.Column("source_code", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("deviation_pct", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dqa_alert_severity", "dealer_quote_authority_v1_market_alerts", ["severity"], unique=False)
    op.create_index("ix_dqa_alert_resolved", "dealer_quote_authority_v1_market_alerts", ["resolved_at"], unique=False)
    op.create_index("ix_dqa_alert_pair", "dealer_quote_authority_v1_market_alerts", ["pair"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_dqa_alert_pair", table_name="dealer_quote_authority_v1_market_alerts")
    op.drop_index("ix_dqa_alert_resolved", table_name="dealer_quote_authority_v1_market_alerts")
    op.drop_index("ix_dqa_alert_severity", table_name="dealer_quote_authority_v1_market_alerts")
    op.drop_table("dealer_quote_authority_v1_market_alerts")
    op.drop_index("ix_dqa_dev_calculated", table_name="dealer_quote_authority_v1_deviations")
    op.drop_index("ix_dqa_dev_source", table_name="dealer_quote_authority_v1_deviations")
    op.drop_index("ix_dqa_dev_pair", table_name="dealer_quote_authority_v1_deviations")
    op.drop_table("dealer_quote_authority_v1_deviations")
    op.drop_index("ix_dqa_ref_captured", table_name="dealer_quote_authority_v1_reference_quotes")
    op.drop_index("ix_dqa_ref_pair", table_name="dealer_quote_authority_v1_reference_quotes")
    op.drop_index("ix_dqa_ref_source", table_name="dealer_quote_authority_v1_reference_quotes")
    op.drop_table("dealer_quote_authority_v1_reference_quotes")
