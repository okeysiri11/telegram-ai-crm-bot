"""rbac_v2_foundation

Revision ID: ee4b1cc39c9b
Revises: 3138ab9befc6
Create Date: 2026-07-12 16:35:49.021301

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ee4b1cc39c9b'
down_revision: Union[str, None] = '3138ab9befc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_ROLES: tuple[tuple[str, str, str], ...] = (
    ("OWNER", "Owner", "Full platform ownership"),
    ("ADMIN", "Administrator", "Platform administration"),
    ("MANAGER", "Manager", "CRM and deal management"),
    ("LAWYER", "Lawyer", "Legal module access"),
    ("DRONE_ENGINEER", "Drone Engineer", "Drone operations access"),
    ("BEAUTY_MANAGER", "Beauty Manager", "Beauty vertical management"),
    ("ACCOUNTANT", "Accountant", "Finance and ledger access"),
    ("PARTNER", "Partner", "Partner portal access"),
)

DEFAULT_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("crm.read", "Read CRM data"),
    ("crm.write", "Create and update CRM data"),
    ("users.read", "View users"),
    ("users.write", "Create and update users"),
    ("roles.manage", "Manage roles and assignments"),
    ("finance.read", "View finance accounts and transactions"),
    ("finance.write", "Create and update finance records"),
    ("ledger.read", "View ledger entries"),
    ("ledger.write", "Create and update ledger entries"),
    ("partner.read", "View partners"),
    ("partner.write", "Create and update partners"),
    ("deal.read", "View deals"),
    ("deal.write", "Create and update deals"),
    ("commission.read", "View commissions"),
    ("commission.write", "Create and update commissions"),
)

DEFAULT_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "OWNER": frozenset(code for code, _ in DEFAULT_PERMISSIONS),
    "ADMIN": frozenset(code for code, _ in DEFAULT_PERMISSIONS),
    "MANAGER": frozenset(
        {
            "crm.read",
            "crm.write",
            "users.read",
            "deal.read",
            "deal.write",
            "partner.read",
            "commission.read",
        }
    ),
    "LAWYER": frozenset({"crm.read", "deal.read", "ledger.read"}),
    "DRONE_ENGINEER": frozenset({"crm.read", "deal.read", "deal.write"}),
    "BEAUTY_MANAGER": frozenset(
        {"crm.read", "crm.write", "deal.read", "deal.write", "partner.read"}
    ),
    "ACCOUNTANT": frozenset(
        {
            "finance.read",
            "finance.write",
            "ledger.read",
            "ledger.write",
            "commission.read",
        }
    ),
    "PARTNER": frozenset({"partner.read", "deal.read"}),
}


def _seed_rbac_defaults() -> None:
    bind = op.get_bind()
    roles_table = sa.table(
        "roles",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
    )
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

    role_ids: dict[str, uuid.UUID] = {}
    for code, name, description in DEFAULT_ROLES:
        existing = bind.execute(
            sa.text("SELECT id FROM roles WHERE code = :code"),
            {"code": code},
        ).first()
        if existing:
            role_ids[code] = existing[0]
            continue
        role_id = uuid.uuid4()
        bind.execute(
            roles_table.insert().values(
                id=role_id,
                code=code,
                name=name,
                description=description,
            )
        )
        role_ids[code] = role_id

    permission_ids: dict[str, uuid.UUID] = {}
    for code, description in DEFAULT_PERMISSIONS:
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

    for role_code, permission_codes in DEFAULT_ROLE_PERMISSIONS.items():
        role_id = role_ids[role_code]
        for permission_code in permission_codes:
            permission_id = permission_ids[permission_code]
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
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('permissions',
    sa.Column('code', sa.String(length=128), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code', name='uq_permissions_code')
    )
    op.create_index('ix_permissions_code', 'permissions', ['code'], unique=False)
    op.create_table('role_permissions',
    sa.Column('role_id', sa.UUID(), nullable=False),
    sa.Column('permission_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('role_id', 'permission_id'),
    sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permissions')
    )
    op.create_index('ix_role_permissions_permission_id', 'role_permissions', ['permission_id'], unique=False)
    op.create_index('ix_role_permissions_role_id', 'role_permissions', ['role_id'], unique=False)
    op.drop_index(op.f('ix_rbac_role_grants_role_id'), table_name='rbac_role_grants')
    op.drop_table('rbac_role_grants')
    op.drop_index(op.f('ix_rbac_permissions_level'), table_name='rbac_permissions')
    op.drop_index(op.f('ix_rbac_permissions_module'), table_name='rbac_permissions')
    op.drop_table('rbac_permissions')
    op.add_column('roles', sa.Column('code', sa.String(length=64), nullable=True))
    op.add_column('roles', sa.Column('name', sa.String(length=128), nullable=True))
    op.execute(
        sa.text(
            "UPDATE roles SET code = role_name, name = role_name "
            "WHERE code IS NULL"
        )
    )
    op.alter_column('roles', 'code', nullable=False)
    op.alter_column('roles', 'name', nullable=False)
    op.alter_column('roles', 'description',
               existing_type=sa.VARCHAR(length=512),
               type_=sa.Text(),
               existing_nullable=True)
    op.drop_index(op.f('ix_roles_role_name'), table_name='roles')
    op.drop_constraint(op.f('uq_roles_role_name'), 'roles', type_='unique')
    op.create_index('ix_roles_code', 'roles', ['code'], unique=False)
    op.create_unique_constraint('uq_roles_code', 'roles', ['code'])
    op.drop_column('roles', 'role_name')
    op.add_column('user_roles', sa.Column('assigned_by', sa.UUID(), nullable=True))
    op.drop_constraint(op.f('user_roles_assigned_by_id_fkey'), 'user_roles', type_='foreignkey')
    op.create_foreign_key(None, 'user_roles', 'users', ['assigned_by'], ['id'], ondelete='SET NULL')
    op.drop_column('user_roles', 'assigned_by_id')
    op.alter_column('users', 'username',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=64),
               existing_nullable=True)
    op.alter_column('users', 'full_name',
               existing_type=sa.VARCHAR(length=512),
               type_=sa.String(length=255),
               existing_nullable=True)
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_constraint(op.f('users_deleted_by_id_fkey'), 'users', type_='foreignkey')
    op.drop_column('users', 'is_deleted')
    op.drop_column('users', 'deleted_by_id')
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'deleted_at')
    _seed_rbac_defaults()
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('deleted_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('deleted_by_id', sa.UUID(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('is_deleted', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.create_foreign_key(op.f('users_deleted_by_id_fkey'), 'users', 'users', ['deleted_by_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.alter_column('users', 'full_name',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=512),
               existing_nullable=True)
    op.alter_column('users', 'username',
               existing_type=sa.String(length=64),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)
    op.add_column('user_roles', sa.Column('assigned_by_id', sa.UUID(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'user_roles', type_='foreignkey')
    op.create_foreign_key(op.f('user_roles_assigned_by_id_fkey'), 'user_roles', 'users', ['assigned_by_id'], ['id'], ondelete='SET NULL')
    op.drop_column('user_roles', 'assigned_by')
    op.add_column('roles', sa.Column('role_name', sa.VARCHAR(length=64), autoincrement=False, nullable=False))
    op.drop_constraint('uq_roles_code', 'roles', type_='unique')
    op.drop_index('ix_roles_code', table_name='roles')
    op.create_unique_constraint(op.f('uq_roles_role_name'), 'roles', ['role_name'], postgresql_nulls_not_distinct=False)
    op.create_index(op.f('ix_roles_role_name'), 'roles', ['role_name'], unique=False)
    op.alter_column('roles', 'description',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=512),
               existing_nullable=True)
    op.drop_column('roles', 'name')
    op.drop_column('roles', 'code')
    op.create_table('rbac_permissions',
    sa.Column('code', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.Column('level', sa.VARCHAR(length=32), autoincrement=False, nullable=False),
    sa.Column('module', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.Column('entity', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.Column('parent_code', sa.VARCHAR(length=128), autoincrement=False, nullable=True),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['parent_code'], ['rbac_permissions.code'], name=op.f('rbac_permissions_parent_code_fkey'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('code', name=op.f('rbac_permissions_pkey'))
    )
    op.create_index(op.f('ix_rbac_permissions_module'), 'rbac_permissions', ['module'], unique=False)
    op.create_index(op.f('ix_rbac_permissions_level'), 'rbac_permissions', ['level'], unique=False)
    op.create_table('rbac_role_grants',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('role_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('permission_code', sa.VARCHAR(length=128), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['permission_code'], ['rbac_permissions.code'], name=op.f('rbac_role_grants_permission_code_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('rbac_role_grants_role_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('rbac_role_grants_pkey')),
    sa.UniqueConstraint('role_id', 'permission_code', name=op.f('uq_rbac_role_grants'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_rbac_role_grants_role_id'), 'rbac_role_grants', ['role_id'], unique=False)
    op.drop_index('ix_role_permissions_role_id', table_name='role_permissions')
    op.drop_index('ix_role_permissions_permission_id', table_name='role_permissions')
    op.drop_table('role_permissions')
    op.drop_index('ix_permissions_code', table_name='permissions')
    op.drop_table('permissions')
    # ### end Alembic commands ###
