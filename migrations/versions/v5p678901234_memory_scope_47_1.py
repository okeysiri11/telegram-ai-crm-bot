"""AI Agent Memory Architecture — scope columns — Sprint 47.1.

Adds tenant_id (canonical org identifier, Sprint 47.0 Decision 5) plus
vertical/customer_id to the project_memory and user_memory tables, per
docs/SPRINT_47_MULTI_DOMAIN_EXPANSION_PLAN.md. All columns are
nullable/additive — no backfill, no NOT NULL constraint, no data loss risk.
tenant_id is a real FK to partner_tenant_engine_v1_tenants.id, following the
schema template already used by ai_sales_agent_v1_customer_preferences
(database/models/ai_sales_agent.py::CustomerPreference).

project_memory already has a `client_id` column (the CUSTOMER identifier for
that table) — no separate customer_id column is added there, to avoid a
second, duplicate representation of the same thing (see
database/models/project_memory.py::ProjectMemoryRow). user_memory has no
customer-like column, so it gets tenant_id + vertical + customer_id.

Revision ID: v5p678901234
Revises: u4o567890123
Create Date: 2026-08-09 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "v5p678901234"
down_revision: Union[str, None] = "u4o567890123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE_EXTRA_COLUMNS = {
    "project_memory": (),
    "user_memory": (sa.Column("customer_id", sa.String(length=128), nullable=True),),
}


def upgrade() -> None:
    bind = op.get_bind()
    for table, extra_columns in _TABLE_EXTRA_COLUMNS.items():
        exists = bind.execute(
            sa.text("SELECT to_regclass(:t) IS NOT NULL"), {"t": table}
        ).scalar()
        if not exists:
            continue
        with op.batch_alter_table(table) as batch:
            batch.add_column(
                sa.Column(
                    "tenant_id",
                    UUID(as_uuid=True),
                    sa.ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="SET NULL"),
                    nullable=True,
                )
            )
            batch.add_column(sa.Column("vertical", sa.String(length=64), nullable=True))
            for col in extra_columns:
                batch.add_column(col)
        op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])


def downgrade() -> None:
    # Non-destructive by policy in this repo (see u4o567890123's downgrade) —
    # do not drop scope columns from production tables.
    pass
