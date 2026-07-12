"""automotive_sales_pipeline_stages_v2

Revision ID: b9e4f1a23c07
Revises: f7a3c2d81e04
Create Date: 2026-07-12 22:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b9e4f1a23c07"
down_revision: Union[str, None] = "f7a3c2d81e04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STAGE_MAP = {
    "NEW": "NEW_LEAD",
    "CONTRACT": "CONTRACT_SIGNED",
}


def _migrate_stages(table: str, column: str) -> None:
    bind = op.get_bind()
    for old, new in _STAGE_MAP.items():
        bind.execute(
            sa.text(f"UPDATE {table} SET {column} = :new WHERE {column} = :old"),
            {"old": old, "new": new},
        )


def upgrade() -> None:
    _migrate_stages("automotive_sales_v1_leads", "pipeline_stage")
    _migrate_stages("automotive_sales_v1_sales_pipeline", "from_stage")
    _migrate_stages("automotive_sales_v1_sales_pipeline", "to_stage")


def downgrade() -> None:
    bind = op.get_bind()
    reverse = {new: old for old, new in _STAGE_MAP.items()}
    for table, column in (
        ("automotive_sales_v1_leads", "pipeline_stage"),
        ("automotive_sales_v1_sales_pipeline", "from_stage"),
        ("automotive_sales_v1_sales_pipeline", "to_stage"),
    ):
        for new, old in reverse.items():
            bind.execute(
                sa.text(f"UPDATE {table} SET {column} = :old WHERE {column} = :new"),
                {"old": old, "new": new},
            )
