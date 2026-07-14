"""deal_engine_v1

Revision ID: f1b234567890
Revises: f0a123456789
Create Date: 2026-07-14 13:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f1b234567890"
down_revision: Union[str, None] = "f0a123456789"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deal_engine_v1_deals",
        sa.Column("lead_id", sa.UUID(), nullable=True),
        sa.Column("vertical", sa.String(length=50), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("manager_id", sa.UUID(), nullable=True),
        sa.Column("partner_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="NEW"),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["lead_id"], ["lead_engine_v1_leads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["client_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["partner_id"], ["automotive_partner_v1_partners.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deal_engine_v1_lead", "deal_engine_v1_deals", ["lead_id"])
    op.create_index("ix_deal_engine_v1_vertical", "deal_engine_v1_deals", ["vertical"])
    op.create_index("ix_deal_engine_v1_status", "deal_engine_v1_deals", ["status"])
    op.create_index("ix_deal_engine_v1_client", "deal_engine_v1_deals", ["client_id"])
    op.create_index("ix_deal_engine_v1_manager", "deal_engine_v1_deals", ["manager_id"])
    op.create_index("ix_deal_engine_v1_partner", "deal_engine_v1_deals", ["partner_id"])
    op.create_index("ix_deal_engine_v1_created", "deal_engine_v1_deals", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_deal_engine_v1_created", table_name="deal_engine_v1_deals")
    op.drop_index("ix_deal_engine_v1_partner", table_name="deal_engine_v1_deals")
    op.drop_index("ix_deal_engine_v1_manager", table_name="deal_engine_v1_deals")
    op.drop_index("ix_deal_engine_v1_client", table_name="deal_engine_v1_deals")
    op.drop_index("ix_deal_engine_v1_status", table_name="deal_engine_v1_deals")
    op.drop_index("ix_deal_engine_v1_vertical", table_name="deal_engine_v1_deals")
    op.drop_index("ix_deal_engine_v1_lead", table_name="deal_engine_v1_deals")
    op.drop_table("deal_engine_v1_deals")
