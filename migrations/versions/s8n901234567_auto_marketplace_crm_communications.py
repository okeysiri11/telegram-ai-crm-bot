"""Auto Marketplace CRM communications, meetings, and reminders (additive).

Revision ID: s8n901234567
Revises: r7m890123456
Create Date: 2026-08-24 12:16:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "s8n901234567"
down_revision: Union[str, None] = "r7m890123456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts_cols():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    conn = op.get_bind()

    def _exists(name: str) -> bool:
        return conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar() is not None

    if not _exists("auto_marketplace_crm_calls"):
        op.create_table(
            "auto_marketplace_crm_calls",
            sa.Column("call_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("customer_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("lead_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("deal_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("agent_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("direction", sa.String(32), nullable=False, server_default="outbound"),
            sa.Column("status", sa.String(64), nullable=False, server_default="logged"),
            sa.Column("duration_sec", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("summary", sa.Text(), nullable=False, server_default=""),
            sa.Column("started_at", sa.Float(), nullable=True),
            sa.Column("ended_at", sa.Float(), nullable=True),
            sa.Column("created_ts", sa.Float(), nullable=False, server_default="0"),
            sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_ts_cols(),
        )
        op.create_index("ix_am_crm_calls_tenant", "auto_marketplace_crm_calls", ["tenant_id"])
        op.create_index("ix_am_crm_calls_tenant_customer", "auto_marketplace_crm_calls", ["tenant_id", "customer_id"])
        op.create_index("ix_am_crm_calls_tenant_lead", "auto_marketplace_crm_calls", ["tenant_id", "lead_id"])
        op.create_index("ix_am_crm_calls_tenant_deal", "auto_marketplace_crm_calls", ["tenant_id", "deal_id"])

    if not _exists("auto_marketplace_crm_emails"):
        op.create_table(
            "auto_marketplace_crm_emails",
            sa.Column("email_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("customer_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("lead_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("deal_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("agent_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("subject", sa.String(255), nullable=False, server_default=""),
            sa.Column("body", sa.Text(), nullable=False, server_default=""),
            sa.Column("direction", sa.String(32), nullable=False, server_default="outbound"),
            sa.Column("status", sa.String(64), nullable=False, server_default="logged"),
            sa.Column("sender", sa.String(255), nullable=False, server_default=""),
            sa.Column("recipient", sa.String(255), nullable=False, server_default=""),
            sa.Column("created_ts", sa.Float(), nullable=False, server_default="0"),
            sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_ts_cols(),
        )
        op.create_index("ix_am_crm_emails_tenant", "auto_marketplace_crm_emails", ["tenant_id"])
        op.create_index(
            "ix_am_crm_emails_tenant_customer",
            "auto_marketplace_crm_emails",
            ["tenant_id", "customer_id"],
        )
        op.create_index("ix_am_crm_emails_tenant_status", "auto_marketplace_crm_emails", ["tenant_id", "status"])

    if not _exists("auto_marketplace_crm_meetings"):
        op.create_table(
            "auto_marketplace_crm_meetings",
            sa.Column("meeting_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("customer_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("lead_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("deal_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("agent_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("title", sa.String(255), nullable=False, server_default=""),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("scheduled_at", sa.Float(), nullable=False, server_default="0"),
            sa.Column("duration_min", sa.Integer(), nullable=False, server_default="30"),
            sa.Column("location", sa.String(255), nullable=False, server_default=""),
            sa.Column("status", sa.String(64), nullable=False, server_default="scheduled"),
            sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_ts", sa.Float(), nullable=False, server_default="0"),
            sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_ts_cols(),
        )
        op.create_index("ix_am_crm_meetings_tenant", "auto_marketplace_crm_meetings", ["tenant_id"])
        op.create_index(
            "ix_am_crm_meetings_tenant_customer",
            "auto_marketplace_crm_meetings",
            ["tenant_id", "customer_id"],
        )
        op.create_index("ix_am_crm_meetings_tenant_status", "auto_marketplace_crm_meetings", ["tenant_id", "status"])
        op.create_index("ix_am_crm_meetings_tenant_agent", "auto_marketplace_crm_meetings", ["tenant_id", "agent_id"])

    if not _exists("auto_marketplace_crm_reminders"):
        op.create_table(
            "auto_marketplace_crm_reminders",
            sa.Column("reminder_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("task_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("customer_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("lead_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("deal_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("title", sa.String(255), nullable=False, server_default=""),
            sa.Column("message", sa.Text(), nullable=False, server_default=""),
            sa.Column("assigned_agent_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("trigger_at", sa.Float(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(64), nullable=False, server_default="pending"),
            sa.Column("triggered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_ts", sa.Float(), nullable=False, server_default="0"),
            sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_ts_cols(),
        )
        op.create_index("ix_am_crm_reminders_tenant", "auto_marketplace_crm_reminders", ["tenant_id"])
        op.create_index(
            "ix_am_crm_reminders_tenant_status",
            "auto_marketplace_crm_reminders",
            ["tenant_id", "status"],
        )
        op.create_index(
            "ix_am_crm_reminders_tenant_customer",
            "auto_marketplace_crm_reminders",
            ["tenant_id", "customer_id"],
        )
        op.create_index(
            "ix_am_crm_reminders_tenant_trigger",
            "auto_marketplace_crm_reminders",
            ["tenant_id", "trigger_at"],
        )


def downgrade() -> None:
    conn = op.get_bind()

    def _exists(name: str) -> bool:
        return conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar() is not None

    for table in (
        "auto_marketplace_crm_reminders",
        "auto_marketplace_crm_meetings",
        "auto_marketplace_crm_emails",
        "auto_marketplace_crm_calls",
    ):
        if _exists(table):
            op.drop_table(table)
