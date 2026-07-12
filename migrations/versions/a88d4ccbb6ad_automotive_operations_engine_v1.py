"""automotive_operations_engine_v1

Revision ID: a88d4ccbb6ad
Revises: df23cfb47bd6
Create Date: 2026-07-12 23:26:21.784941

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a88d4ccbb6ad"
down_revision: Union[str, None] = "df23cfb47bd6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_EVENT_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("vehicle.created", "Emit or subscribe to vehicle created events"),
    ("vehicle.arrived", "Emit or subscribe to vehicle arrived events"),
    ("vehicle.listed", "Emit or subscribe to vehicle listed events"),
    ("vehicle.reserved", "Emit or subscribe to vehicle reserved events"),
    ("vehicle.sold", "Emit or subscribe to vehicle sold events"),
    ("vehicle.delivered", "Emit or subscribe to vehicle delivered events"),
)

NEW_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "MANAGER": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "ADMIN": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "OWNER": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
}


def _seed_operations_event_permissions() -> None:
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
    for code, description in NEW_EVENT_PERMISSIONS:
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
                continue
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
    op.create_table('automotive_operations_v1_vehicle_operations',
    sa.Column('vehicle_id', sa.UUID(), nullable=False),
    sa.Column('current_state', sa.String(length=30), nullable=False),
    sa.Column('assigned_manager_id', sa.BigInteger(), nullable=True),
    sa.Column('state_entered_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('sla_deadline', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['vehicle_id'], ['automotive_v1_vehicles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('vehicle_id', name='uq_automotive_operations_v1_ops_vehicle_id')
    )
    op.create_index('ix_automotive_operations_v1_ops_manager', 'automotive_operations_v1_vehicle_operations', ['assigned_manager_id'], unique=False)
    op.create_index('ix_automotive_operations_v1_ops_sla', 'automotive_operations_v1_vehicle_operations', ['sla_deadline'], unique=False)
    op.create_index('ix_automotive_operations_v1_ops_state', 'automotive_operations_v1_vehicle_operations', ['current_state'], unique=False)
    op.create_table('automotive_operations_v1_vehicle_state_history',
    sa.Column('operation_id', sa.UUID(), nullable=False),
    sa.Column('vehicle_id', sa.UUID(), nullable=False),
    sa.Column('from_state', sa.String(length=30), nullable=True),
    sa.Column('to_state', sa.String(length=30), nullable=False),
    sa.Column('changed_by', sa.BigInteger(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['operation_id'], ['automotive_operations_v1_vehicle_operations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['vehicle_id'], ['automotive_v1_vehicles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automotive_operations_v1_state_hist_operation', 'automotive_operations_v1_vehicle_state_history', ['operation_id'], unique=False)
    op.create_index('ix_automotive_operations_v1_state_hist_vehicle', 'automotive_operations_v1_vehicle_state_history', ['vehicle_id'], unique=False)
    op.create_table('automotive_operations_v1_vehicle_tasks',
    sa.Column('operation_id', sa.UUID(), nullable=False),
    sa.Column('vehicle_id', sa.UUID(), nullable=False),
    sa.Column('task_type', sa.String(length=30), nullable=False),
    sa.Column('title', sa.String(length=300), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('priority', sa.String(length=10), nullable=False),
    sa.Column('assigned_to', sa.BigInteger(), nullable=True),
    sa.Column('sla_deadline', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('auto_generated', sa.Boolean(), nullable=False),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['operation_id'], ['automotive_operations_v1_vehicle_operations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['vehicle_id'], ['automotive_v1_vehicles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automotive_operations_v1_tasks_assigned', 'automotive_operations_v1_vehicle_tasks', ['assigned_to'], unique=False)
    op.create_index('ix_automotive_operations_v1_tasks_operation', 'automotive_operations_v1_vehicle_tasks', ['operation_id'], unique=False)
    op.create_index('ix_automotive_operations_v1_tasks_sla', 'automotive_operations_v1_vehicle_tasks', ['sla_deadline'], unique=False)
    op.create_index('ix_automotive_operations_v1_tasks_status', 'automotive_operations_v1_vehicle_tasks', ['status'], unique=False)
    op.create_index('ix_automotive_operations_v1_tasks_type', 'automotive_operations_v1_vehicle_tasks', ['task_type'], unique=False)
    op.create_index('ix_automotive_operations_v1_tasks_vehicle', 'automotive_operations_v1_vehicle_tasks', ['vehicle_id'], unique=False)
    op.create_table('automotive_operations_v1_vehicle_attachments',
    sa.Column('operation_id', sa.UUID(), nullable=False),
    sa.Column('vehicle_id', sa.UUID(), nullable=False),
    sa.Column('task_id', sa.UUID(), nullable=True),
    sa.Column('file_url', sa.String(length=512), nullable=False),
    sa.Column('attachment_type', sa.String(length=30), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=True),
    sa.Column('uploaded_by', sa.BigInteger(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['operation_id'], ['automotive_operations_v1_vehicle_operations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['task_id'], ['automotive_operations_v1_vehicle_tasks.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['vehicle_id'], ['automotive_v1_vehicles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automotive_operations_v1_attachments_operation', 'automotive_operations_v1_vehicle_attachments', ['operation_id'], unique=False)
    op.create_index('ix_automotive_operations_v1_attachments_task', 'automotive_operations_v1_vehicle_attachments', ['task_id'], unique=False)
    op.create_index('ix_automotive_operations_v1_attachments_vehicle', 'automotive_operations_v1_vehicle_attachments', ['vehicle_id'], unique=False)
    op.create_table('automotive_operations_v1_vehicle_checklists',
    sa.Column('operation_id', sa.UUID(), nullable=False),
    sa.Column('task_id', sa.UUID(), nullable=True),
    sa.Column('item_key', sa.String(length=50), nullable=False),
    sa.Column('label', sa.String(length=300), nullable=False),
    sa.Column('is_required', sa.Boolean(), nullable=False),
    sa.Column('is_completed', sa.Boolean(), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_by', sa.BigInteger(), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['operation_id'], ['automotive_operations_v1_vehicle_operations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['task_id'], ['automotive_operations_v1_vehicle_tasks.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automotive_operations_v1_checklists_operation', 'automotive_operations_v1_vehicle_checklists', ['operation_id'], unique=False)
    op.create_index('ix_automotive_operations_v1_checklists_task', 'automotive_operations_v1_vehicle_checklists', ['task_id'], unique=False)
    _seed_operations_event_permissions()


def downgrade() -> None:
    op.drop_index('ix_automotive_operations_v1_checklists_task', table_name='automotive_operations_v1_vehicle_checklists')
    op.drop_index('ix_automotive_operations_v1_checklists_operation', table_name='automotive_operations_v1_vehicle_checklists')
    op.drop_table('automotive_operations_v1_vehicle_checklists')
    op.drop_index('ix_automotive_operations_v1_attachments_vehicle', table_name='automotive_operations_v1_vehicle_attachments')
    op.drop_index('ix_automotive_operations_v1_attachments_task', table_name='automotive_operations_v1_vehicle_attachments')
    op.drop_index('ix_automotive_operations_v1_attachments_operation', table_name='automotive_operations_v1_vehicle_attachments')
    op.drop_table('automotive_operations_v1_vehicle_attachments')
    op.drop_index('ix_automotive_operations_v1_tasks_vehicle', table_name='automotive_operations_v1_vehicle_tasks')
    op.drop_index('ix_automotive_operations_v1_tasks_type', table_name='automotive_operations_v1_vehicle_tasks')
    op.drop_index('ix_automotive_operations_v1_tasks_status', table_name='automotive_operations_v1_vehicle_tasks')
    op.drop_index('ix_automotive_operations_v1_tasks_sla', table_name='automotive_operations_v1_vehicle_tasks')
    op.drop_index('ix_automotive_operations_v1_tasks_operation', table_name='automotive_operations_v1_vehicle_tasks')
    op.drop_index('ix_automotive_operations_v1_tasks_assigned', table_name='automotive_operations_v1_vehicle_tasks')
    op.drop_table('automotive_operations_v1_vehicle_tasks')
    op.drop_index('ix_automotive_operations_v1_state_hist_vehicle', table_name='automotive_operations_v1_vehicle_state_history')
    op.drop_index('ix_automotive_operations_v1_state_hist_operation', table_name='automotive_operations_v1_vehicle_state_history')
    op.drop_table('automotive_operations_v1_vehicle_state_history')
    op.drop_index('ix_automotive_operations_v1_ops_state', table_name='automotive_operations_v1_vehicle_operations')
    op.drop_index('ix_automotive_operations_v1_ops_sla', table_name='automotive_operations_v1_vehicle_operations')
    op.drop_index('ix_automotive_operations_v1_ops_manager', table_name='automotive_operations_v1_vehicle_operations')
    op.drop_table('automotive_operations_v1_vehicle_operations')
    # ### end Alembic commands ###
