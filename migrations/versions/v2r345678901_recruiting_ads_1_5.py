"""Recruiting ads lookup indexes — Sprint Recruiting 1.5 (additive).

Revision ID: v2r345678901
Revises: u1q234567890
Create Date: 2026-08-27 12:50:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "v2r345678901"
down_revision: Union[str, None] = "u1q234567890"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_recruiting_ops_payload_campaign
        ON recruiting_ops_records ((payload->>'campaign_id'))
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_recruiting_ops_payload_project
        ON recruiting_ops_records ((payload->>'project_key'))
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_recruiting_ops_payload_event_id
        ON recruiting_ops_records ((payload->>'event_id'))
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_recruiting_ops_payload_event_id")
    op.execute("DROP INDEX IF EXISTS ix_recruiting_ops_payload_project")
    op.execute("DROP INDEX IF EXISTS ix_recruiting_ops_payload_campaign")
