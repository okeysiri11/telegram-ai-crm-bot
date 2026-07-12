"""permission_engine_foundation

Revision ID: 32c851505370
Revises: 59ed827af999
Create Date: 2026-07-12 17:16:37.353071

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "32c851505370"
down_revision: Union[str, None] = "59ed827af999"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_ROLES: tuple[tuple[str, str, str], ...] = (
    ("OWNER", "Owner", "Full platform access"),
    ("ADMIN", "Administrator", "Administrative access"),
    ("MANAGER", "Manager", "Deal and team management"),
    ("ACCOUNTANT", "Accountant", "Finance and ledger access"),
    ("LAWYER", "Lawyer", "Legal and audit read access"),
    ("PARTNER", "Partner", "Partner portal access"),
    ("OPERATOR", "Operator", "Operational deal processing"),
    ("VIEWER", "Viewer", "Read-only access"),
)

DEFAULT_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("VIEW_DEALS", "View deals"),
    ("CREATE_DEALS", "Create deals"),
    ("EDIT_DEALS", "Edit deals"),
    ("DELETE_DEALS", "Delete deals"),
    ("VIEW_LEDGER", "View ledger"),
    ("EDIT_LEDGER", "Edit ledger"),
    ("VIEW_COMMISSIONS", "View commissions"),
    ("PAY_COMMISSIONS", "Pay commissions"),
    ("VIEW_USERS", "View users"),
    ("CREATE_USERS", "Create users"),
    ("EDIT_USERS", "Edit users"),
    ("DELETE_USERS", "Delete users"),
    ("VIEW_AUDIT", "View audit logs"),
    ("EXPORT_AUDIT", "Export audit logs"),
    ("VIEW_REPORTS", "View reports"),
    ("EXPORT_REPORTS", "Export reports"),
    ("MANAGE_SETTINGS", "Manage platform settings"),
)

DEFAULT_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "OWNER": frozenset(code for code, _ in DEFAULT_PERMISSIONS),
    "ADMIN": frozenset(code for code, _ in DEFAULT_PERMISSIONS),
    "MANAGER": frozenset(
        {
            "VIEW_DEALS",
            "CREATE_DEALS",
            "EDIT_DEALS",
            "VIEW_COMMISSIONS",
            "VIEW_REPORTS",
        }
    ),
    "ACCOUNTANT": frozenset(
        {
            "VIEW_DEALS",
            "VIEW_LEDGER",
            "EDIT_LEDGER",
            "VIEW_COMMISSIONS",
            "PAY_COMMISSIONS",
            "VIEW_REPORTS",
            "EXPORT_REPORTS",
        }
    ),
    "LAWYER": frozenset({"VIEW_DEALS", "VIEW_AUDIT", "EXPORT_AUDIT"}),
    "PARTNER": frozenset({"VIEW_DEALS", "VIEW_COMMISSIONS"}),
    "OPERATOR": frozenset({"VIEW_DEALS", "CREATE_DEALS", "EDIT_DEALS"}),
    "VIEWER": frozenset({"VIEW_DEALS", "VIEW_REPORTS"}),
}


def _seed_permission_engine() -> None:
    bind = op.get_bind()
    roles_table = sa.table(
        "permission_engine_roles",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
    )
    permissions_table = sa.table(
        "permission_engine_permissions",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.String()),
        sa.column("description", sa.Text()),
    )
    role_permissions_table = sa.table(
        "permission_engine_role_permissions",
        sa.column("role_id", sa.UUID()),
        sa.column("permission_id", sa.UUID()),
    )

    role_ids: dict[str, uuid.UUID] = {}
    for code, name, description in DEFAULT_ROLES:
        row = bind.execute(
            sa.text("SELECT id FROM permission_engine_roles WHERE code = :code"),
            {"code": code},
        ).first()
        if row:
            role_ids[code] = row[0]
            continue
        role_id = uuid.uuid4()
        bind.execute(
            roles_table.insert().values(
                id=role_id, code=code, name=name, description=description
            )
        )
        role_ids[code] = role_id

    permission_ids: dict[str, uuid.UUID] = {}
    for code, description in DEFAULT_PERMISSIONS:
        row = bind.execute(
            sa.text("SELECT id FROM permission_engine_permissions WHERE code = :code"),
            {"code": code},
        ).first()
        if row:
            permission_ids[code] = row[0]
            continue
        permission_id = uuid.uuid4()
        bind.execute(
            permissions_table.insert().values(
                id=permission_id, code=code, description=description
            )
        )
        permission_ids[code] = permission_id

    for role_code, permission_codes in DEFAULT_ROLE_PERMISSIONS.items():
        role_id = role_ids[role_code]
        for permission_code in permission_codes:
            permission_id = permission_ids[permission_code]
            exists = bind.execute(
                sa.text(
                    "SELECT 1 FROM permission_engine_role_permissions "
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
    op.create_table(
        "permission_engine_permissions",
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_permission_engine_permissions_code"),
    )
    op.create_index(
        "ix_permission_engine_permissions_code",
        "permission_engine_permissions",
        ["code"],
        unique=False,
    )
    op.create_table(
        "permission_engine_roles",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_permission_engine_roles_code"),
    )
    op.create_index(
        "ix_permission_engine_roles_code",
        "permission_engine_roles",
        ["code"],
        unique=False,
    )
    op.create_table(
        "permission_engine_role_permissions",
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("permission_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"], ["permission_engine_permissions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["permission_engine_roles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
        sa.UniqueConstraint(
            "role_id", "permission_id", name="uq_permission_engine_role_permissions"
        ),
    )
    op.create_index(
        "ix_permission_engine_role_permissions_permission_id",
        "permission_engine_role_permissions",
        ["permission_id"],
        unique=False,
    )
    op.create_index(
        "ix_permission_engine_role_permissions_role_id",
        "permission_engine_role_permissions",
        ["role_id"],
        unique=False,
    )
    op.create_table(
        "permission_engine_user_roles",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["permission_engine_roles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )
    op.create_index(
        "ix_permission_engine_user_roles_role_id",
        "permission_engine_user_roles",
        ["role_id"],
        unique=False,
    )
    op.create_index(
        "ix_permission_engine_user_roles_user_id",
        "permission_engine_user_roles",
        ["user_id"],
        unique=False,
    )
    _seed_permission_engine()


def downgrade() -> None:
    op.drop_index(
        "ix_permission_engine_user_roles_user_id",
        table_name="permission_engine_user_roles",
    )
    op.drop_index(
        "ix_permission_engine_user_roles_role_id",
        table_name="permission_engine_user_roles",
    )
    op.drop_table("permission_engine_user_roles")
    op.drop_index(
        "ix_permission_engine_role_permissions_role_id",
        table_name="permission_engine_role_permissions",
    )
    op.drop_index(
        "ix_permission_engine_role_permissions_permission_id",
        table_name="permission_engine_role_permissions",
    )
    op.drop_table("permission_engine_role_permissions")
    op.drop_index("ix_permission_engine_roles_code", table_name="permission_engine_roles")
    op.drop_table("permission_engine_roles")
    op.drop_index(
        "ix_permission_engine_permissions_code",
        table_name="permission_engine_permissions",
    )
    op.drop_table("permission_engine_permissions")
