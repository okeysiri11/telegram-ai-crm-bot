"""sla_tracking_v1

Revision ID: f5f678901234
Revises: f4e567890123
Create Date: 2026-07-14 13:00:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f5f678901234"
down_revision: Union[str, None] = "f4e567890123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sla_tracking_v1_entries",
        sa.Column("lead_id", sa.UUID(), nullable=False),
        sa.Column("deal_id", sa.UUID(), nullable=True),
        sa.Column("vertical", sa.String(length=50), nullable=False),
        sa.Column("manager_id", sa.UUID(), nullable=True),
        sa.Column("lead_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_contact_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_response_minutes", sa.Integer(), nullable=True),
        sa.Column("manager_assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deal_closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_traffic_light", sa.String(length=10), nullable=True),
        sa.Column("is_overdue", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("manager_telegram_id", sa.BigInteger(), nullable=True),
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
        sa.ForeignKeyConstraint(["deal_id"], ["deal_engine_v1_deals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["lead_engine_v1_leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lead_id"),
    )
    op.create_index("ix_sla_tracking_v1_lead", "sla_tracking_v1_entries", ["lead_id"])
    op.create_index("ix_sla_tracking_v1_deal", "sla_tracking_v1_entries", ["deal_id"])
    op.create_index("ix_sla_tracking_v1_vertical", "sla_tracking_v1_entries", ["vertical"])
    op.create_index("ix_sla_tracking_v1_manager", "sla_tracking_v1_entries", ["manager_id"])
    op.create_index("ix_sla_tracking_v1_overdue", "sla_tracking_v1_entries", ["is_overdue"])
    op.create_index(
        "ix_sla_tracking_v1_traffic",
        "sla_tracking_v1_entries",
        ["response_traffic_light"],
    )
    op.create_index(
        "ix_sla_tracking_v1_lead_created",
        "sla_tracking_v1_entries",
        ["lead_created_at"],
    )

    conn = op.get_bind()
    leads = conn.execute(
        sa.text(
            """
            SELECT id, vertical, assigned_manager_id, status, created_at, updated_at
            FROM lead_engine_v1_leads
            """
        )
    ).fetchall()

    sla_table = sa.table(
        "sla_tracking_v1_entries",
        sa.column("id", sa.UUID()),
        sa.column("lead_id", sa.UUID()),
        sa.column("deal_id", sa.UUID()),
        sa.column("vertical", sa.String()),
        sa.column("manager_id", sa.UUID()),
        sa.column("lead_created_at", sa.DateTime(timezone=True)),
        sa.column("first_contact_at", sa.DateTime(timezone=True)),
        sa.column("first_response_minutes", sa.Integer()),
        sa.column("manager_assigned_at", sa.DateTime(timezone=True)),
        sa.column("deal_closed_at", sa.DateTime(timezone=True)),
        sa.column("response_traffic_light", sa.String()),
        sa.column("is_overdue", sa.Boolean()),
        sa.column("manager_telegram_id", sa.BigInteger()),
    )

    rows = []
    for lead in leads:
        lead_id, vertical, manager_id, status, created_at, updated_at = lead
        first_contact = None
        response_minutes = None
        traffic = None
        if status and status != "NEW":
            first_contact = updated_at
            if created_at and updated_at:
                delta = updated_at - created_at
                response_minutes = max(int(delta.total_seconds() // 60), 0)
                if response_minutes < 15:
                    traffic = "green"
                elif response_minutes <= 60:
                    traffic = "yellow"
                else:
                    traffic = "red"
        rows.append({
            "id": uuid.uuid4(),
            "lead_id": lead_id,
            "deal_id": None,
            "vertical": vertical,
            "manager_id": manager_id,
            "lead_created_at": created_at,
            "first_contact_at": first_contact,
            "first_response_minutes": response_minutes,
            "manager_assigned_at": updated_at if manager_id else None,
            "deal_closed_at": None,
            "response_traffic_light": traffic,
            "is_overdue": False,
            "manager_telegram_id": None,
        })

    if rows:
        op.bulk_insert(sla_table, rows)

    deals = conn.execute(
        sa.text(
            """
            SELECT d.id, d.lead_id, d.closed_at
            FROM deal_engine_v1_deals d
            WHERE d.closed_at IS NOT NULL AND d.lead_id IS NOT NULL
            """
        )
    ).fetchall()
    for deal_id, lead_id, closed_at in deals:
        op.execute(
            sa.text(
                """
                UPDATE sla_tracking_v1_entries
                SET deal_id = :deal_id, deal_closed_at = :closed_at
                WHERE lead_id = :lead_id
                """
            ).bindparams(deal_id=deal_id, closed_at=closed_at, lead_id=lead_id)
        )


def downgrade() -> None:
    op.drop_index("ix_sla_tracking_v1_lead_created", table_name="sla_tracking_v1_entries")
    op.drop_index("ix_sla_tracking_v1_traffic", table_name="sla_tracking_v1_entries")
    op.drop_index("ix_sla_tracking_v1_overdue", table_name="sla_tracking_v1_entries")
    op.drop_index("ix_sla_tracking_v1_manager", table_name="sla_tracking_v1_entries")
    op.drop_index("ix_sla_tracking_v1_vertical", table_name="sla_tracking_v1_entries")
    op.drop_index("ix_sla_tracking_v1_deal", table_name="sla_tracking_v1_entries")
    op.drop_index("ix_sla_tracking_v1_lead", table_name="sla_tracking_v1_entries")
    op.drop_table("sla_tracking_v1_entries")
