"""Auto Marketplace CRM tasks and activities (additive).

Revision ID: r7m890123456
Revises: q6l789012345
Create Date: 2026-08-24 10:50:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "r7m890123456"
down_revision: Union[str, None] = "q6l789012345"
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

    if not _exists("auto_marketplace_crm_tasks"):
        op.create_table(
            "auto_marketplace_crm_tasks",
            sa.Column("task_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("title", sa.String(255), nullable=False, server_default=""),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("status", sa.String(64), nullable=False, server_default="pending"),
            sa.Column("priority", sa.String(64), nullable=False, server_default="normal"),
            sa.Column("customer_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("lead_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("deal_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("assigned_agent_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("created_by", sa.String(64), nullable=False, server_default=""),
            sa.Column("due_at", sa.Float(), nullable=True),
            sa.Column("completed_at", sa.Float(), nullable=True),
            sa.Column("created_ts", sa.Float(), nullable=False, server_default="0"),
            sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_ts_cols(),
        )
        op.create_index("ix_am_crm_tasks_tenant", "auto_marketplace_crm_tasks", ["tenant_id"])
        op.create_index("ix_am_crm_tasks_tenant_status", "auto_marketplace_crm_tasks", ["tenant_id", "status"])
        op.create_index(
            "ix_am_crm_tasks_tenant_assignee",
            "auto_marketplace_crm_tasks",
            ["tenant_id", "assigned_agent_id"],
        )
        op.create_index("ix_am_crm_tasks_tenant_customer", "auto_marketplace_crm_tasks", ["tenant_id", "customer_id"])
        op.create_index("ix_am_crm_tasks_tenant_lead", "auto_marketplace_crm_tasks", ["tenant_id", "lead_id"])
        op.create_index("ix_am_crm_tasks_tenant_deal", "auto_marketplace_crm_tasks", ["tenant_id", "deal_id"])

    if not _exists("auto_marketplace_crm_activities"):
        op.create_table(
            "auto_marketplace_crm_activities",
            sa.Column("activity_id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
            sa.Column("activity_type", sa.String(64), nullable=False, server_default="note"),
            sa.Column("customer_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("lead_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("deal_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("task_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("agent_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("subject", sa.String(255), nullable=False, server_default=""),
            sa.Column("body", sa.Text(), nullable=False, server_default=""),
            sa.Column("idempotency_key", sa.String(255), nullable=False, server_default=""),
            sa.Column("created_ts", sa.Float(), nullable=False, server_default="0"),
            sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            *_ts_cols(),
        )
        op.create_index("ix_am_crm_activities_tenant", "auto_marketplace_crm_activities", ["tenant_id"])
        op.create_index(
            "ix_am_crm_activities_tenant_type",
            "auto_marketplace_crm_activities",
            ["tenant_id", "activity_type"],
        )
        op.create_index(
            "ix_am_crm_activities_tenant_customer",
            "auto_marketplace_crm_activities",
            ["tenant_id", "customer_id"],
        )
        op.create_index(
            "ix_am_crm_activities_tenant_lead",
            "auto_marketplace_crm_activities",
            ["tenant_id", "lead_id"],
        )
        op.create_index(
            "ix_am_crm_activities_tenant_deal",
            "auto_marketplace_crm_activities",
            ["tenant_id", "deal_id"],
        )
        op.create_index(
            "ix_am_crm_activities_tenant_task",
            "auto_marketplace_crm_activities",
            ["tenant_id", "task_id"],
        )
        op.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_am_crm_activities_tenant_idempotency "
            "ON auto_marketplace_crm_activities (tenant_id, idempotency_key) "
            "WHERE idempotency_key <> ''"
        )


def downgrade() -> None:
    conn = op.get_bind()

    def _exists(name: str) -> bool:
        return conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar() is not None

    for table in ("auto_marketplace_crm_activities", "auto_marketplace_crm_tasks"):
        if _exists(table):
            op.drop_table(table)
