"""partner_cabinet_v1

Revision ID: f8i901234567
Revises: f7h890123456
Create Date: 2026-07-14 14:30:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f8i901234567"
down_revision: Union[str, None] = "f7h890123456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLE_MAP = {
    "INSURANCE": "insurance",
    "LEASING": "leasing",
    "CREDIT": "banks",
    "LOGISTICS": "logistics",
    "LEGAL": "legal",
    "DEALER": "dealers",
    "DELIVERY": "logistics",
}


def upgrade() -> None:
    op.create_table(
        "partner_cabinet_v1_profiles",
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("cabinet_role", sa.String(length=50), nullable=False),
        sa.Column("commission_rate", sa.Numeric(8, 4), nullable=True),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("blocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("blocked_by_telegram_id", sa.BigInteger(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["partner_id"],
            ["automotive_partner_v1_partners.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("partner_id", name="uq_partner_cabinet_v1_partner"),
        sa.UniqueConstraint("telegram_user_id", name="uq_partner_cabinet_v1_telegram"),
    )
    op.create_index(
        "ix_partner_cabinet_v1_role",
        "partner_cabinet_v1_profiles",
        ["cabinet_role"],
    )
    op.create_index(
        "ix_partner_cabinet_v1_blocked",
        "partner_cabinet_v1_profiles",
        ["is_blocked"],
    )

    op.create_table(
        "partner_cabinet_v1_commissions",
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("deal_id", sa.UUID(), nullable=False),
        sa.Column("revenue_entry_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACCRUED"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_by_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["deal_id"], ["deal_engine_v1_deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["partner_id"],
            ["automotive_partner_v1_partners.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["revenue_entry_id"],
            ["revenue_engine_v1_entries.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("revenue_entry_id", name="uq_partner_cabinet_v1_revenue"),
    )
    op.create_index(
        "ix_partner_cabinet_v1_comm_partner",
        "partner_cabinet_v1_commissions",
        ["partner_id"],
    )
    op.create_index(
        "ix_partner_cabinet_v1_comm_status",
        "partner_cabinet_v1_commissions",
        ["status"],
    )
    op.create_index(
        "ix_partner_cabinet_v1_comm_deal",
        "partner_cabinet_v1_commissions",
        ["deal_id"],
    )

    conn = op.get_bind()
    partners = conn.execute(
        sa.text(
            "SELECT id, partner_type FROM automotive_partner_v1_partners WHERE is_active = true"
        )
    ).fetchall()

    profile_table = sa.table(
        "partner_cabinet_v1_profiles",
        sa.column("id", sa.UUID()),
        sa.column("partner_id", sa.UUID()),
        sa.column("telegram_user_id", sa.BigInteger()),
        sa.column("cabinet_role", sa.String()),
        sa.column("commission_rate", sa.Numeric(8, 4)),
        sa.column("is_blocked", sa.Boolean()),
    )
    rows = []
    for partner_id, partner_type in partners:
        role = ROLE_MAP.get(partner_type, "dealers")
        default_rate = 0.30 if role in {"insurance", "dealers", "service_stations"} else 0.25
        rows.append({
            "id": uuid.uuid4(),
            "partner_id": partner_id,
            "telegram_user_id": None,
            "cabinet_role": role,
            "commission_rate": default_rate,
            "is_blocked": False,
        })
    if rows:
        op.bulk_insert(profile_table, rows)

    revenue_rows = conn.execute(
        sa.text(
            """
            SELECT r.id, r.deal_id, r.partner_income, r.currency, d.partner_id
            FROM revenue_engine_v1_entries r
            JOIN deal_engine_v1_deals d ON d.id = r.deal_id
            WHERE d.partner_id IS NOT NULL AND r.partner_income > 0
            """
        )
    ).fetchall()

    comm_table = sa.table(
        "partner_cabinet_v1_commissions",
        sa.column("id", sa.UUID()),
        sa.column("partner_id", sa.UUID()),
        sa.column("deal_id", sa.UUID()),
        sa.column("revenue_entry_id", sa.UUID()),
        sa.column("amount", sa.Numeric(18, 2)),
        sa.column("currency", sa.String()),
        sa.column("status", sa.String()),
    )
    comm_rows = [
        {
            "id": uuid.uuid4(),
            "partner_id": partner_id,
            "deal_id": deal_id,
            "revenue_entry_id": rev_id,
            "amount": amount,
            "currency": currency or "USD",
            "status": "ACCRUED",
        }
        for rev_id, deal_id, amount, currency, partner_id in revenue_rows
    ]
    if comm_rows:
        op.bulk_insert(comm_table, comm_rows)


def downgrade() -> None:
    op.drop_index("ix_partner_cabinet_v1_comm_deal", table_name="partner_cabinet_v1_commissions")
    op.drop_index("ix_partner_cabinet_v1_comm_status", table_name="partner_cabinet_v1_commissions")
    op.drop_index("ix_partner_cabinet_v1_comm_partner", table_name="partner_cabinet_v1_commissions")
    op.drop_table("partner_cabinet_v1_commissions")

    op.drop_index("ix_partner_cabinet_v1_blocked", table_name="partner_cabinet_v1_profiles")
    op.drop_index("ix_partner_cabinet_v1_role", table_name="partner_cabinet_v1_profiles")
    op.drop_table("partner_cabinet_v1_profiles")
