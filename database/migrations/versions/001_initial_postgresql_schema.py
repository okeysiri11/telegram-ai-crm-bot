"""Initial PostgreSQL schema — UUID PKs, indexes, FKs, cascades.

Revision ID: 001_initial_pg
Revises:
Create Date: 2026-07-12
"""

from typing import Sequence, Union

from alembic import op

import database.models  # noqa: F401
from database.base import Base

revision: str = "001_initial_pg"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
