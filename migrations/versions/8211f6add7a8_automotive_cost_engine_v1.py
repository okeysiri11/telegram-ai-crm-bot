"""automotive_cost_engine_v1

Revision ID: 8211f6add7a8
Revises: 042bf97aa37b
Create Date: 2026-07-12 20:22:51.834801

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8211f6add7a8'
down_revision: Union[str, None] = '042bf97aa37b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('automotive_cost_v1_margin_rules',
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('rule_type', sa.String(length=20), nullable=False),
    sa.Column('min_base_amount', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('max_base_amount', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('margin_percent', sa.Numeric(precision=8, scale=4), nullable=True),
    sa.Column('margin_fixed', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automotive_cost_v1_mr_is_active', 'automotive_cost_v1_margin_rules', ['is_active'], unique=False)
    op.create_index('ix_automotive_cost_v1_mr_priority', 'automotive_cost_v1_margin_rules', ['priority'], unique=False)
    op.create_table('automotive_cost_v1_vehicle_costs',
    sa.Column('vehicle_id', sa.UUID(), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('purchase_amount', sa.Numeric(precision=20, scale=2), nullable=False),
    sa.Column('subtotal_amount', sa.Numeric(precision=20, scale=2), nullable=False),
    sa.Column('margin_amount', sa.Numeric(precision=20, scale=2), nullable=False),
    sa.Column('total_amount', sa.Numeric(precision=20, scale=2), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('total_amount >= 0', name='ck_automotive_cost_v1_vc_total'),
    sa.ForeignKeyConstraint(['vehicle_id'], ['automotive_v1_vehicles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('vehicle_id', name='uq_automotive_cost_v1_vehicle_costs_vehicle_id')
    )
    op.create_index('ix_automotive_cost_v1_vc_status', 'automotive_cost_v1_vehicle_costs', ['status'], unique=False)
    op.create_table('automotive_cost_v1_cost_items',
    sa.Column('vehicle_cost_id', sa.UUID(), nullable=False),
    sa.Column('item_type', sa.String(length=30), nullable=False),
    sa.Column('label', sa.String(length=100), nullable=True),
    sa.Column('amount', sa.Numeric(precision=20, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('is_calculated', sa.Boolean(), nullable=False),
    sa.Column('calculation_method', sa.String(length=50), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['vehicle_cost_id'], ['automotive_cost_v1_vehicle_costs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automotive_cost_v1_ci_item_type', 'automotive_cost_v1_cost_items', ['item_type'], unique=False)
    op.create_index('ix_automotive_cost_v1_ci_vehicle_cost_id', 'automotive_cost_v1_cost_items', ['vehicle_cost_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_automotive_cost_v1_ci_vehicle_cost_id', table_name='automotive_cost_v1_cost_items')
    op.drop_index('ix_automotive_cost_v1_ci_item_type', table_name='automotive_cost_v1_cost_items')
    op.drop_table('automotive_cost_v1_cost_items')
    op.drop_index('ix_automotive_cost_v1_vc_status', table_name='automotive_cost_v1_vehicle_costs')
    op.drop_table('automotive_cost_v1_vehicle_costs')
    op.drop_index('ix_automotive_cost_v1_mr_priority', table_name='automotive_cost_v1_margin_rules')
    op.drop_index('ix_automotive_cost_v1_mr_is_active', table_name='automotive_cost_v1_margin_rules')
    op.drop_table('automotive_cost_v1_margin_rules')
