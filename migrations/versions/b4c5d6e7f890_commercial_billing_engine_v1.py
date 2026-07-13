"""commercial_billing_engine_v1

Revision ID: b4c5d6e7f890
Revises: a2b3c4d5e6f7
Create Date: 2026-07-13 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b4c5d6e7f890"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "commercial_billing_engine_v1_payments",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("company_id", sa.UUID(), nullable=True),
        sa.Column("subscription_id", sa.UUID(), nullable=True),
        sa.Column("plan_code", sa.String(length=30), nullable=False),
        sa.Column("pricing_model", sa.String(length=30), nullable=False),
        sa.Column("payment_method", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("reviewed_by", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["multi_company_v1_companies.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["tenant_billing_engine_v1_subscriptions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["partner_tenant_engine_v1_tenants.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_commercial_billing_payments_user",
        "commercial_billing_engine_v1_payments",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_commercial_billing_payments_tenant",
        "commercial_billing_engine_v1_payments",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_commercial_billing_payments_status",
        "commercial_billing_engine_v1_payments",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_commercial_billing_payments_plan",
        "commercial_billing_engine_v1_payments",
        ["plan_code"],
        unique=False,
    )

    op.create_table(
        "commercial_billing_engine_v1_payment_receipts",
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("uploaded_by", sa.BigInteger(), nullable=False),
        sa.Column("telegram_file_id", sa.String(length=255), nullable=False),
        sa.Column("telegram_file_unique_id", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("storage_path", sa.String(length=512), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["payment_id"],
            ["commercial_billing_engine_v1_payments.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_commercial_billing_receipts_payment",
        "commercial_billing_engine_v1_payment_receipts",
        ["payment_id"],
        unique=False,
    )
    op.create_index(
        "ix_commercial_billing_receipts_user",
        "commercial_billing_engine_v1_payment_receipts",
        ["uploaded_by"],
        unique=False,
    )

    op.create_table(
        "commercial_billing_engine_v1_subscription_history",
        sa.Column("subscription_id", sa.UUID(), nullable=True),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("old_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["tenant_billing_engine_v1_subscriptions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["partner_tenant_engine_v1_tenants.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_commercial_billing_sub_history_tenant",
        "commercial_billing_engine_v1_subscription_history",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_commercial_billing_sub_history_subscription",
        "commercial_billing_engine_v1_subscription_history",
        ["subscription_id"],
        unique=False,
    )

    op.create_table(
        "commercial_billing_engine_v1_billing_events",
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("entity_id", sa.String(length=120), nullable=False),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["partner_tenant_engine_v1_tenants.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_commercial_billing_events_type",
        "commercial_billing_engine_v1_billing_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_commercial_billing_events_entity",
        "commercial_billing_engine_v1_billing_events",
        ["entity_type", "entity_id"],
        unique=False,
    )
    op.create_index(
        "ix_commercial_billing_events_tenant",
        "commercial_billing_engine_v1_billing_events",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_commercial_billing_events_tenant",
        table_name="commercial_billing_engine_v1_billing_events",
    )
    op.drop_index(
        "ix_commercial_billing_events_entity",
        table_name="commercial_billing_engine_v1_billing_events",
    )
    op.drop_index(
        "ix_commercial_billing_events_type",
        table_name="commercial_billing_engine_v1_billing_events",
    )
    op.drop_table("commercial_billing_engine_v1_billing_events")

    op.drop_index(
        "ix_commercial_billing_sub_history_subscription",
        table_name="commercial_billing_engine_v1_subscription_history",
    )
    op.drop_index(
        "ix_commercial_billing_sub_history_tenant",
        table_name="commercial_billing_engine_v1_subscription_history",
    )
    op.drop_table("commercial_billing_engine_v1_subscription_history")

    op.drop_index(
        "ix_commercial_billing_receipts_user",
        table_name="commercial_billing_engine_v1_payment_receipts",
    )
    op.drop_index(
        "ix_commercial_billing_receipts_payment",
        table_name="commercial_billing_engine_v1_payment_receipts",
    )
    op.drop_table("commercial_billing_engine_v1_payment_receipts")

    op.drop_index(
        "ix_commercial_billing_payments_plan",
        table_name="commercial_billing_engine_v1_payments",
    )
    op.drop_index(
        "ix_commercial_billing_payments_status",
        table_name="commercial_billing_engine_v1_payments",
    )
    op.drop_index(
        "ix_commercial_billing_payments_tenant",
        table_name="commercial_billing_engine_v1_payments",
    )
    op.drop_index(
        "ix_commercial_billing_payments_user",
        table_name="commercial_billing_engine_v1_payments",
    )
    op.drop_table("commercial_billing_engine_v1_payments")
