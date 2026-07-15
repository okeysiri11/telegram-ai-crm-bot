"""Architecture scaffold placeholder migration

Revision ID: f9u123456789
Revises: f9t012345678
Create Date: 2026-07-15 18:00:00.000000

NOTE: Night architecture task — NO schema destructive changes.
Permission tables already exist as permission_engine_*.
Role/Permission domain models live as dataclasses under src/platform/permissions.
This migration records architecture epoch only (revision marker).
"""
from __future__ import annotations

from typing import Sequence, Union

revision: str = "f9u123456789"
down_revision: Union[str, None] = "f9t012345678"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Intentional no-op: scaffold docs & src/ domains only.
    # Future migration may create domain-specific schemas after strangler cutover.
    pass


def downgrade() -> None:
    pass
