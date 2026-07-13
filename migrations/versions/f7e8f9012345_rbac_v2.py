"""rbac_v2

Revision ID: f7e8f9012345
Revises: c6d7e8f90123
Create Date: 2026-07-13 16:00:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "f7e8f9012345"
down_revision: Union[str, None] = "c6d7e8f90123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rbac_v2_permissions",
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("parent_code", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_code"],
            ["rbac_v2_permissions.code"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_rbac_v2_permissions_code"),
    )
    op.create_index("ix_rbac_v2_permissions_category", "rbac_v2_permissions", ["category"], unique=False)
    op.create_index("ix_rbac_v2_permissions_parent", "rbac_v2_permissions", ["parent_code"], unique=False)

    op.create_table(
        "rbac_v2_role_grants",
        sa.Column("role_code", sa.String(length=64), nullable=False),
        sa.Column("permission_code", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_code"],
            ["rbac_v2_permissions.code"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("role_code", "permission_code"),
        sa.UniqueConstraint("role_code", "permission_code", name="uq_rbac_v2_role_grants"),
    )
    op.create_index("ix_rbac_v2_role_grants_role", "rbac_v2_role_grants", ["role_code"], unique=False)

    op.create_table(
        "rbac_v2_role_inheritance",
        sa.Column("role_code", sa.String(length=64), nullable=False),
        sa.Column("parent_role_code", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("role_code", "parent_role_code"),
        sa.UniqueConstraint("role_code", "parent_role_code", name="uq_rbac_v2_role_inheritance"),
    )
    op.create_index("ix_rbac_v2_role_inheritance_role", "rbac_v2_role_inheritance", ["role_code"], unique=False)

    op.create_table(
        "rbac_v2_role_templates",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("role_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("permission_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_rbac_v2_role_templates_code"),
    )
    op.create_index("ix_rbac_v2_role_templates_code", "rbac_v2_role_templates", ["code"], unique=False)

    _seed_rbac_v2_python()


def _seed_rbac_v2_python() -> None:
    import json

    from database.seeds.rbac_v2 import (
        RBAC_V2_DIRECT_ROLE_PERMISSIONS,
        RBAC_V2_PERMISSIONS,
        RBAC_V2_ROLE_INHERITANCE,
        RBAC_V2_ROLE_TEMPLATES,
        RBAC_V2_ROLES,
    )

    bind = op.get_bind()

    for code, category, parent_code, description in RBAC_V2_PERMISSIONS:
        exists = bind.execute(
            sa.text("SELECT 1 FROM rbac_v2_permissions WHERE code = :code"),
            {"code": code},
        ).first()
        if exists:
            continue
        bind.execute(
            sa.text(
                """
                INSERT INTO rbac_v2_permissions (id, code, category, parent_code, description)
                VALUES (:id, :code, :category, :parent_code, :description)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "code": code,
                "category": category,
                "parent_code": parent_code,
                "description": description,
            },
        )

    for code, name, description in RBAC_V2_ROLES:
        exists = bind.execute(
            sa.text("SELECT 1 FROM permission_engine_roles WHERE code = :code"),
            {"code": code},
        ).first()
        if exists:
            continue
        bind.execute(
            sa.text(
                """
                INSERT INTO permission_engine_roles (id, code, name, description)
                VALUES (:id, :code, :name, :description)
                """
            ),
            {"id": str(uuid.uuid4()), "code": code, "name": name, "description": description},
        )

    for role_code, parents in RBAC_V2_ROLE_INHERITANCE.items():
        for parent in parents:
            exists = bind.execute(
                sa.text(
                    "SELECT 1 FROM rbac_v2_role_inheritance "
                    "WHERE role_code = :role_code AND parent_role_code = :parent"
                ),
                {"role_code": role_code, "parent": parent},
            ).first()
            if exists:
                continue
            bind.execute(
                sa.text(
                    """
                    INSERT INTO rbac_v2_role_inheritance (role_code, parent_role_code)
                    VALUES (:role_code, :parent_role_code)
                    """
                ),
                {"role_code": role_code, "parent_role_code": parent},
            )

    for role_code, permission_codes in RBAC_V2_DIRECT_ROLE_PERMISSIONS.items():
        for permission_code in permission_codes:
            exists = bind.execute(
                sa.text(
                    "SELECT 1 FROM rbac_v2_role_grants "
                    "WHERE role_code = :role_code AND permission_code = :permission_code"
                ),
                {"role_code": role_code, "permission_code": permission_code},
            ).first()
            if exists:
                continue
            bind.execute(
                sa.text(
                    """
                    INSERT INTO rbac_v2_role_grants (role_code, permission_code)
                    VALUES (:role_code, :permission_code)
                    """
                ),
                {"role_code": role_code, "permission_code": permission_code},
            )

    for code, name, description, role_codes, permission_codes in RBAC_V2_ROLE_TEMPLATES:
        exists = bind.execute(
            sa.text("SELECT 1 FROM rbac_v2_role_templates WHERE code = :code"),
            {"code": code},
        ).first()
        if exists:
            continue
        bind.execute(
            sa.text(
                """
                INSERT INTO rbac_v2_role_templates
                    (id, code, name, description, role_codes, permission_codes, created_at, updated_at)
                VALUES
                    (:id, :code, :name, :description, CAST(:role_codes AS jsonb),
                     CAST(:permission_codes AS jsonb), now(), now())
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "code": code,
                "name": name,
                "description": description,
                "role_codes": json.dumps(list(role_codes)),
                "permission_codes": json.dumps(list(permission_codes)),
            },
        )


def downgrade() -> None:
    op.drop_index("ix_rbac_v2_role_templates_code", table_name="rbac_v2_role_templates")
    op.drop_table("rbac_v2_role_templates")
    op.drop_index("ix_rbac_v2_role_inheritance_role", table_name="rbac_v2_role_inheritance")
    op.drop_table("rbac_v2_role_inheritance")
    op.drop_index("ix_rbac_v2_role_grants_role", table_name="rbac_v2_role_grants")
    op.drop_table("rbac_v2_role_grants")
    op.drop_index("ix_rbac_v2_permissions_parent", table_name="rbac_v2_permissions")
    op.drop_index("ix_rbac_v2_permissions_category", table_name="rbac_v2_permissions")
    op.drop_table("rbac_v2_permissions")
