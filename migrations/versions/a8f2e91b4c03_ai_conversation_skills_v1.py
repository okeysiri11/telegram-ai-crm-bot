"""ai_conversation_skills_v1

Revision ID: a8f2e91b4c03
Revises: 150b3b288847
Create Date: 2026-07-13 13:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a8f2e91b4c03'
down_revision: Union[str, None] = '150b3b288847'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('ai_conversation_skills_v1_conversation_memory',
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('session_ref', sa.String(length=120), nullable=False),
    sa.Column('conversation_id', sa.String(length=120), nullable=True),
    sa.Column('customer_profile', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('context_summary', sa.Text(), nullable=True),
    sa.Column('emotional_tone', sa.String(length=30), nullable=True),
    sa.Column('communication_style_used', sa.String(length=30), nullable=True),
    sa.Column('active_skill_code', sa.String(length=40), nullable=True),
    sa.Column('turn_count', sa.Integer(), nullable=False),
    sa.Column('memory_items', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['multi_company_v1_companies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['partner_tenant_engine_v1_tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'session_ref', name='uq_ai_conversation_skills_v1_memory_tenant_session')
    )
    op.create_index('ix_ai_conversation_skills_v1_memory_conversation', 'ai_conversation_skills_v1_conversation_memory', ['conversation_id'], unique=False)
    op.create_index('ix_ai_conversation_skills_v1_memory_tenant', 'ai_conversation_skills_v1_conversation_memory', ['tenant_id'], unique=False)
    op.create_table('ai_conversation_skills_v1_personalities',
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('tone', sa.String(length=30), nullable=False),
    sa.Column('communication_style', sa.String(length=30), nullable=False),
    sa.Column('traits', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=False),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['multi_company_v1_companies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['partner_tenant_engine_v1_tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_conversation_skills_v1_personalities_default', 'ai_conversation_skills_v1_personalities', ['is_default'], unique=False)
    op.create_index('ix_ai_conversation_skills_v1_personalities_tenant', 'ai_conversation_skills_v1_personalities', ['tenant_id'], unique=False)
    op.create_table('ai_conversation_skills_v1_skills',
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('skill_code', sa.String(length=40), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('system_prompt', sa.Text(), nullable=True),
    sa.Column('is_enabled', sa.Boolean(), nullable=False),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['multi_company_v1_companies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['partner_tenant_engine_v1_tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'skill_code', name='uq_ai_conversation_skills_v1_skills_tenant_code')
    )
    op.create_index('ix_ai_conversation_skills_v1_skills_code', 'ai_conversation_skills_v1_skills', ['skill_code'], unique=False)
    op.create_index('ix_ai_conversation_skills_v1_skills_tenant', 'ai_conversation_skills_v1_skills', ['tenant_id'], unique=False)
    op.create_table('ai_conversation_skills_v1_response_templates',
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('skill_id', sa.UUID(), nullable=True),
    sa.Column('template_code', sa.String(length=80), nullable=False),
    sa.Column('channel', sa.String(length=30), nullable=True),
    sa.Column('language', sa.String(length=10), nullable=False),
    sa.Column('template_text', sa.Text(), nullable=False),
    sa.Column('variables', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['multi_company_v1_companies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['skill_id'], ['ai_conversation_skills_v1_skills.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['tenant_id'], ['partner_tenant_engine_v1_tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'template_code', name='uq_ai_conversation_skills_v1_templates_tenant_code')
    )
    op.create_index('ix_ai_conversation_skills_v1_templates_skill', 'ai_conversation_skills_v1_response_templates', ['skill_id'], unique=False)
    op.create_index('ix_ai_conversation_skills_v1_templates_tenant', 'ai_conversation_skills_v1_response_templates', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_ai_conversation_skills_v1_templates_tenant', table_name='ai_conversation_skills_v1_response_templates')
    op.drop_index('ix_ai_conversation_skills_v1_templates_skill', table_name='ai_conversation_skills_v1_response_templates')
    op.drop_table('ai_conversation_skills_v1_response_templates')
    op.drop_index('ix_ai_conversation_skills_v1_skills_tenant', table_name='ai_conversation_skills_v1_skills')
    op.drop_index('ix_ai_conversation_skills_v1_skills_code', table_name='ai_conversation_skills_v1_skills')
    op.drop_table('ai_conversation_skills_v1_skills')
    op.drop_index('ix_ai_conversation_skills_v1_personalities_tenant', table_name='ai_conversation_skills_v1_personalities')
    op.drop_index('ix_ai_conversation_skills_v1_personalities_default', table_name='ai_conversation_skills_v1_personalities')
    op.drop_table('ai_conversation_skills_v1_personalities')
    op.drop_index('ix_ai_conversation_skills_v1_memory_tenant', table_name='ai_conversation_skills_v1_conversation_memory')
    op.drop_index('ix_ai_conversation_skills_v1_memory_conversation', table_name='ai_conversation_skills_v1_conversation_memory')
    op.drop_table('ai_conversation_skills_v1_conversation_memory')
