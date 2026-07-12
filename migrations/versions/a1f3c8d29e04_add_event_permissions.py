"""add event permissions to rbac registry

Revision ID: a1f3c8d29e04
Revises: ee4b1cc39c9b
Create Date: 2026-07-12 16:45:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1f3c8d29e04"
down_revision: Union[str, None] = "ee4b1cc39c9b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("deal.created", "Emit or subscribe to deal created events"),
    ("deal.updated", "Emit or subscribe to deal updated events"),
    ("payment.received", "Emit or subscribe to payment received events"),
    ("partner.assigned", "Emit or subscribe to partner assigned events"),
    ("commission.created", "Emit or subscribe to commission created events"),
    ("ledger.entry.created", "Emit or subscribe to ledger entry created events"),
)

NEW_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "MANAGER": frozenset(
        {
            "deal.created",
            "deal.updated",
            "partner.assigned",
            "commission.created",
        }
    ),
    "LAWYER": frozenset({"deal.created", "deal.updated", "ledger.entry.created"}),
    "DRONE_ENGINEER": frozenset({"deal.created", "deal.updated"}),
    "BEAUTY_MANAGER": frozenset(
        {"deal.created", "deal.updated", "partner.assigned"}
    ),
    "ACCOUNTANT": frozenset(
        {
            "ledger.entry.created",
            "commission.created",
            "payment.received",
        }
    ),
    "PARTNER": frozenset({"deal.created", "partner.assigned"}),
}


def _seed_event_permissions() -> None:
    bind = op.get_bind()
    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.String()),
        sa.column("description", sa.Text()),
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.UUID()),
        sa.column("permission_id", sa.UUID()),
    )

    permission_ids: dict[str, uuid.UUID] = {}
    for code, description in NEW_PERMISSIONS:
        existing = bind.execute(
            sa.text("SELECT id FROM permissions WHERE code = :code"),
            {"code": code},
        ).first()
        if existing:
            permission_ids[code] = existing[0]
            continue
        permission_id = uuid.uuid4()
        bind.execute(
            permissions_table.insert().values(
                id=permission_id,
                code=code,
                description=description,
            )
        )
        permission_ids[code] = permission_id

    for role_code, permission_codes in NEW_ROLE_PERMISSIONS.items():
        role_row = bind.execute(
            sa.text("SELECT id FROM roles WHERE code = :code"),
            {"code": role_code},
        ).first()
        if not role_row:
            continue
        role_id = role_row[0]
        for permission_code in permission_codes:
            permission_id = permission_ids.get(permission_code)
            if permission_id is None:
                perm_row = bind.execute(
                    sa.text("SELECT id FROM permissions WHERE code = :code"),
                    {"code": permission_code},
                ).first()
                if not perm_row:
                    continue
                permission_id = perm_row[0]
            exists = bind.execute(
                sa.text(
                    "SELECT 1 FROM role_permissions "
                    "WHERE role_id = :role_id AND permission_id = :permission_id"
                ),
                {"role_id": role_id, "permission_id": permission_id},
            ).first()
            if exists:
                continue
            bind.execute(
                role_permissions_table.insert().values(
                    role_id=role_id,
                    permission_id=permission_id,
                )
            )


def upgrade() -> None:
    _seed_event_permissions()


def downgrade() -> None:
    bind = op.get_bind()
    codes = [code for code, _ in NEW_PERMISSIONS]
    bind.execute(
        sa.text(
            "DELETE FROM role_permissions "
            "WHERE permission_id IN (SELECT id FROM permissions WHERE code = ANY(:codes))"
        ),
        {"codes": codes},
    )
    bind.execute(
        sa.text("DELETE FROM permissions WHERE code = ANY(:codes)"),
        {"codes": codes},
    )
