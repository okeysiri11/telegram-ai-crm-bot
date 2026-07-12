"""automotive_sales_engine_v1

Revision ID: c4e8a1b92f03
Revises: 8211f6add7a8
Create Date: 2026-07-12 20:23:30.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e8a1b92f03'
down_revision: Union[str, None] = '8211f6add7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('automotive_sales_v1_leads',
    sa.Column('vehicle_id', sa.UUID(), nullable=True),
    sa.Column('customer_name', sa.String(length=255), nullable=False),
    sa.Column('customer_phone', sa.String(length=50), nullable=True),
    sa.Column('customer_email', sa.String(length=255), nullable=True),
    sa.Column('source', sa.String(length=30), nullable=False),
    sa.Column('pipeline_stage', sa.String(length=30), nullable=False),
    sa.Column('assigned_to', sa.BigInteger(), nullable=True),
    sa.Column('budget', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['vehicle_id'], ['automotive_v1_vehicles.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automotive_sales_v1_leads_assigned_to', 'automotive_sales_v1_leads', ['assigned_to'], unique=False)
    op.create_index('ix_automotive_sales_v1_leads_pipeline_stage', 'automotive_sales_v1_leads', ['pipeline_stage'], unique=False)
    op.create_index('ix_automotive_sales_v1_leads_vehicle_id', 'automotive_sales_v1_leads', ['vehicle_id'], unique=False)
    op.create_table('automotive_sales_v1_sales_pipeline',
    sa.Column('lead_id', sa.UUID(), nullable=False),
    sa.Column('from_stage', sa.String(length=30), nullable=True),
    sa.Column('to_stage', sa.String(length=30), nullable=False),
    sa.Column('changed_by', sa.BigInteger(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['lead_id'], ['automotive_sales_v1_leads.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automotive_sales_v1_sp_lead_id', 'automotive_sales_v1_sales_pipeline', ['lead_id'], unique=False)
    op.create_index('ix_automotive_sales_v1_sp_to_stage', 'automotive_sales_v1_sales_pipeline', ['to_stage'], unique=False)
    op.create_table('automotive_sales_v1_test_drives',
    sa.Column('lead_id', sa.UUID(), nullable=False),
    sa.Column('vehicle_id', sa.UUID(), nullable=False),
    sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['lead_id'], ['automotive_sales_v1_leads.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['vehicle_id'], ['automotive_v1_vehicles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automotive_sales_v1_td_lead_id', 'automotive_sales_v1_test_drives', ['lead_id'], unique=False)
    op.create_index('ix_automotive_sales_v1_td_scheduled_at', 'automotive_sales_v1_test_drives', ['scheduled_at'], unique=False)
    op.create_index('ix_automotive_sales_v1_td_status', 'automotive_sales_v1_test_drives', ['status'], unique=False)
    op.create_index('ix_automotive_sales_v1_td_vehicle_id', 'automotive_sales_v1_test_drives', ['vehicle_id'], unique=False)
    op.create_table('automotive_sales_v1_vehicle_reservations',
    sa.Column('lead_id', sa.UUID(), nullable=False),
    sa.Column('vehicle_id', sa.UUID(), nullable=False),
    sa.Column('reserved_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deposit_amount', sa.Numeric(precision=20, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['lead_id'], ['automotive_sales_v1_leads.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['vehicle_id'], ['automotive_v1_vehicles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_automotive_sales_v1_res_lead_id', 'automotive_sales_v1_vehicle_reservations', ['lead_id'], unique=False)
    op.create_index('ix_automotive_sales_v1_res_status', 'automotive_sales_v1_vehicle_reservations', ['status'], unique=False)
    op.create_index('ix_automotive_sales_v1_res_vehicle_id', 'automotive_sales_v1_vehicle_reservations', ['vehicle_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_automotive_sales_v1_res_vehicle_id', table_name='automotive_sales_v1_vehicle_reservations')
    op.drop_index('ix_automotive_sales_v1_res_status', table_name='automotive_sales_v1_vehicle_reservations')
    op.drop_index('ix_automotive_sales_v1_res_lead_id', table_name='automotive_sales_v1_vehicle_reservations')
    op.drop_table('automotive_sales_v1_vehicle_reservations')
    op.drop_index('ix_automotive_sales_v1_td_vehicle_id', table_name='automotive_sales_v1_test_drives')
    op.drop_index('ix_automotive_sales_v1_td_status', table_name='automotive_sales_v1_test_drives')
    op.drop_index('ix_automotive_sales_v1_td_scheduled_at', table_name='automotive_sales_v1_test_drives')
    op.drop_index('ix_automotive_sales_v1_td_lead_id', table_name='automotive_sales_v1_test_drives')
    op.drop_table('automotive_sales_v1_test_drives')
    op.drop_index('ix_automotive_sales_v1_sp_to_stage', table_name='automotive_sales_v1_sales_pipeline')
    op.drop_index('ix_automotive_sales_v1_sp_lead_id', table_name='automotive_sales_v1_sales_pipeline')
    op.drop_table('automotive_sales_v1_sales_pipeline')
    op.drop_index('ix_automotive_sales_v1_leads_vehicle_id', table_name='automotive_sales_v1_leads')
    op.drop_index('ix_automotive_sales_v1_leads_pipeline_stage', table_name='automotive_sales_v1_leads')
    op.drop_index('ix_automotive_sales_v1_leads_assigned_to', table_name='automotive_sales_v1_leads')
    op.drop_table('automotive_sales_v1_leads')
