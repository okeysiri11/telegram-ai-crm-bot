"""communication_hub_v1

Revision ID: 150b3b288847
Revises: 0b0c0c734d6e
Create Date: 2026-07-13 13:44:52.979619

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '150b3b288847'
down_revision: Union[str, None] = '0b0c0c734d6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('communication_hub_v1_campaigns',
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('channel_types', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('message_template', sa.Text(), nullable=True),
    sa.Column('auto_response_enabled', sa.Boolean(), nullable=False),
    sa.Column('routing_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('starts_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.BigInteger(), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['multi_company_v1_companies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['partner_tenant_engine_v1_tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_communication_hub_v1_campaigns_status', 'communication_hub_v1_campaigns', ['status'], unique=False)
    op.create_index('ix_communication_hub_v1_campaigns_tenant', 'communication_hub_v1_campaigns', ['tenant_id'], unique=False)
    op.create_table('communication_hub_v1_channels',
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('channel_type', sa.String(length=30), nullable=False),
    sa.Column('external_id', sa.String(length=120), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['multi_company_v1_companies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['partner_tenant_engine_v1_tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'channel_type', 'external_id', name='uq_communication_hub_v1_channels_tenant_type_ext')
    )
    op.create_index('ix_communication_hub_v1_channels_active', 'communication_hub_v1_channels', ['is_active'], unique=False)
    op.create_index('ix_communication_hub_v1_channels_tenant', 'communication_hub_v1_channels', ['tenant_id'], unique=False)
    op.create_index('ix_communication_hub_v1_channels_type', 'communication_hub_v1_channels', ['channel_type'], unique=False)
    op.create_table('communication_hub_v1_messages',
    sa.Column('channel_id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.String(length=120), nullable=False),
    sa.Column('direction', sa.String(length=20), nullable=False),
    sa.Column('sender_type', sa.String(length=20), nullable=False),
    sa.Column('sender_id', sa.String(length=120), nullable=True),
    sa.Column('message_text', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('sales_lead_id', sa.UUID(), nullable=True),
    sa.Column('automation_lead_id', sa.UUID(), nullable=True),
    sa.Column('assigned_manager_id', sa.BigInteger(), nullable=True),
    sa.Column('campaign_id', sa.UUID(), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['automation_lead_id'], ['lead_automation_engine_v1_leads.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['campaign_id'], ['communication_hub_v1_campaigns.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['channel_id'], ['communication_hub_v1_channels.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id'], ['multi_company_v1_companies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sales_lead_id'], ['ai_sales_agent_v1_sales_leads.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['tenant_id'], ['partner_tenant_engine_v1_tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_communication_hub_v1_messages_channel', 'communication_hub_v1_messages', ['channel_id'], unique=False)
    op.create_index('ix_communication_hub_v1_messages_conversation', 'communication_hub_v1_messages', ['conversation_id'], unique=False)
    op.create_index('ix_communication_hub_v1_messages_manager', 'communication_hub_v1_messages', ['assigned_manager_id'], unique=False)
    op.create_index('ix_communication_hub_v1_messages_sales_lead', 'communication_hub_v1_messages', ['sales_lead_id'], unique=False)
    op.create_index('ix_communication_hub_v1_messages_status', 'communication_hub_v1_messages', ['status'], unique=False)
    op.create_index('ix_communication_hub_v1_messages_tenant', 'communication_hub_v1_messages', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_communication_hub_v1_messages_tenant', table_name='communication_hub_v1_messages')
    op.drop_index('ix_communication_hub_v1_messages_status', table_name='communication_hub_v1_messages')
    op.drop_index('ix_communication_hub_v1_messages_sales_lead', table_name='communication_hub_v1_messages')
    op.drop_index('ix_communication_hub_v1_messages_manager', table_name='communication_hub_v1_messages')
    op.drop_index('ix_communication_hub_v1_messages_conversation', table_name='communication_hub_v1_messages')
    op.drop_index('ix_communication_hub_v1_messages_channel', table_name='communication_hub_v1_messages')
    op.drop_table('communication_hub_v1_messages')
    op.drop_index('ix_communication_hub_v1_channels_type', table_name='communication_hub_v1_channels')
    op.drop_index('ix_communication_hub_v1_channels_tenant', table_name='communication_hub_v1_channels')
    op.drop_index('ix_communication_hub_v1_channels_active', table_name='communication_hub_v1_channels')
    op.drop_table('communication_hub_v1_channels')
    op.drop_index('ix_communication_hub_v1_campaigns_tenant', table_name='communication_hub_v1_campaigns')
    op.drop_index('ix_communication_hub_v1_campaigns_status', table_name='communication_hub_v1_campaigns')
    op.drop_table('communication_hub_v1_campaigns')
