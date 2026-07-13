"""multi_tenant_foundation_v1

Revision ID: c6d7e8f90123
Revises: b4c5d6e7f890
Create Date: 2026-07-13 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c6d7e8f90123"
down_revision: Union[str, None] = "b4c5d6e7f890"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_FK = "tenants.id"
PARTNER_TENANT_TABLE = "partner_tenant_engine_v1_tenants"


def _add_tenant_column(table: str, *, nullable: bool = True, ondelete: str | None = None) -> None:
    fk_name = f"fk_mt_{table[:40]}_tenant"[:63]
    idx_name = f"ix_mt_{table[:40]}_tenant"[:63]
    delete_rule = ondelete or ("CASCADE" if nullable else "RESTRICT")
    op.add_column(table, sa.Column("tenant_id", sa.UUID(), nullable=nullable))
    op.create_foreign_key(
        fk_name,
        table,
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete=delete_rule,
    )
    op.create_index(idx_name, table, ["tenant_id"], unique=False)


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
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
        sa.ForeignKeyConstraint(["company_id"], ["multi_company_v1_companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "code", name="uq_tenants_company_code"),
    )
    op.create_index("ix_tenants_company_id", "tenants", ["company_id"], unique=False)
    op.create_index("ix_tenants_status", "tenants", ["status"], unique=False)

    op.execute(
        f"""
        INSERT INTO tenants (id, company_id, code, name, status, created_at, updated_at)
        SELECT id, company_id, code, name, status, created_at, updated_at
        FROM {PARTNER_TENANT_TABLE}
        """
    )

    op.create_table(
        "tenant_settings",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("branding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("features", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_settings_tenant_id"),
    )
    op.create_index("ix_tenant_settings_tenant_id", "tenant_settings", ["tenant_id"], unique=False)

    op.create_table(
        "tenant_limits",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("max_users", sa.Integer(), nullable=False),
        sa.Column("max_cars", sa.Integer(), nullable=False),
        sa.Column("max_leads", sa.Integer(), nullable=False),
        sa.Column("max_campaigns", sa.Integer(), nullable=False),
        sa.Column("max_documents", sa.Integer(), nullable=False),
        sa.Column("plan_code", sa.String(length=30), nullable=True),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_limits_tenant_id"),
    )
    op.create_index("ix_tenant_limits_tenant_id", "tenant_limits", ["tenant_id"], unique=False)

    _add_tenant_column("users", nullable=True, ondelete="SET NULL")

    op.add_column("car_engine_v1_cars", sa.Column("tenant_id", sa.UUID(), nullable=True))
    op.add_column("car_engine_v1_cars", sa.Column("company_id", sa.UUID(), nullable=True))
    op.drop_constraint("uq_car_engine_v1_cars_vin", "car_engine_v1_cars", type_="unique")
    op.create_foreign_key(
        "fk_car_engine_v1_cars_tenant_id",
        "car_engine_v1_cars",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_car_engine_v1_cars_company_id",
        "car_engine_v1_cars",
        "multi_company_v1_companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_car_engine_v1_cars_tenant", "car_engine_v1_cars", ["tenant_id"], unique=False)
    op.create_unique_constraint(
        "uq_car_engine_v1_cars_tenant_vin",
        "car_engine_v1_cars",
        ["tenant_id", "vin"],
    )

    op.add_column("lead_automation_engine_v1_leads", sa.Column("tenant_id", sa.UUID(), nullable=True))
    op.add_column("lead_automation_engine_v1_leads", sa.Column("company_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_lead_automation_leads_tenant_id",
        "lead_automation_engine_v1_leads",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_lead_automation_leads_company_id",
        "lead_automation_engine_v1_leads",
        "multi_company_v1_companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_lead_automation_engine_v1_leads_tenant",
        "lead_automation_engine_v1_leads",
        ["tenant_id"],
        unique=False,
    )

    for table in ("deals", "deal_engine_deals", "document_engine_v1_documents"):
        _add_tenant_column(table, nullable=True)

    op.add_column("auto_marketing_engine_v1_campaigns", sa.Column("tenant_id", sa.UUID(), nullable=True))
    op.add_column("auto_marketing_engine_v1_campaigns", sa.Column("company_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_auto_marketing_campaigns_tenant_id",
        "auto_marketing_engine_v1_campaigns",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_auto_marketing_campaigns_company_id",
        "auto_marketing_engine_v1_campaigns",
        "multi_company_v1_companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_auto_marketing_engine_v1_campaigns_tenant",
        "auto_marketing_engine_v1_campaigns",
        ["tenant_id"],
        unique=False,
    )

    _add_tenant_column("notification_engine_notifications", nullable=True)
    _add_tenant_column("notifications", nullable=True)
    _add_tenant_column("audit_logs", nullable=True, ondelete="SET NULL")
    _add_tenant_column("events", nullable=True)

    for table in (
        "automotive_analytics_v1_inventory_metrics",
        "automotive_analytics_v1_sales_metrics",
        "automotive_analytics_v1_profitability_metrics",
    ):
        _add_tenant_column(table, nullable=True)


def downgrade() -> None:
    for table in (
        "automotive_analytics_v1_profitability_metrics",
        "automotive_analytics_v1_sales_metrics",
        "automotive_analytics_v1_inventory_metrics",
        "events",
        "audit_logs",
        "notifications",
        "notification_engine_notifications",
    ):
        op.drop_index(f"ix_{table}_tenant_id", table_name=table)
        op.drop_constraint(f"fk_{table}_tenant_id_tenants", table, type_="foreignkey")
        op.drop_column(table, "tenant_id")

    op.drop_index("ix_auto_marketing_engine_v1_campaigns_tenant", table_name="auto_marketing_engine_v1_campaigns")
    op.drop_constraint("fk_auto_marketing_campaigns_company_id", "auto_marketing_engine_v1_campaigns", type_="foreignkey")
    op.drop_constraint("fk_auto_marketing_campaigns_tenant_id", "auto_marketing_engine_v1_campaigns", type_="foreignkey")
    op.drop_column("auto_marketing_engine_v1_campaigns", "company_id")
    op.drop_column("auto_marketing_engine_v1_campaigns", "tenant_id")

    for table in ("document_engine_v1_documents", "deal_engine_deals", "deals"):
        op.drop_index(f"ix_{table}_tenant_id", table_name=table)
        op.drop_constraint(f"fk_{table}_tenant_id_tenants", table, type_="foreignkey")
        op.drop_column(table, "tenant_id")

    op.drop_index("ix_lead_automation_engine_v1_leads_tenant", table_name="lead_automation_engine_v1_leads")
    op.drop_constraint("fk_lead_automation_leads_company_id", "lead_automation_engine_v1_leads", type_="foreignkey")
    op.drop_constraint("fk_lead_automation_leads_tenant_id", "lead_automation_engine_v1_leads", type_="foreignkey")
    op.drop_column("lead_automation_engine_v1_leads", "company_id")
    op.drop_column("lead_automation_engine_v1_leads", "tenant_id")

    op.drop_constraint("uq_car_engine_v1_cars_tenant_vin", "car_engine_v1_cars", type_="unique")
    op.drop_index("ix_car_engine_v1_cars_tenant", table_name="car_engine_v1_cars")
    op.drop_constraint("fk_car_engine_v1_cars_company_id", "car_engine_v1_cars", type_="foreignkey")
    op.drop_constraint("fk_car_engine_v1_cars_tenant_id", "car_engine_v1_cars", type_="foreignkey")
    op.drop_column("car_engine_v1_cars", "company_id")
    op.drop_column("car_engine_v1_cars", "tenant_id")
    op.create_unique_constraint("uq_car_engine_v1_cars_vin", "car_engine_v1_cars", ["vin"])

    op.drop_constraint("fk_users_tenant_id_tenants", "users", type_="foreignkey")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_column("users", "tenant_id")

    op.drop_index("ix_tenant_limits_tenant_id", table_name="tenant_limits")
    op.drop_table("tenant_limits")
    op.drop_index("ix_tenant_settings_tenant_id", table_name="tenant_settings")
    op.drop_table("tenant_settings")
    op.drop_index("ix_tenants_status", table_name="tenants")
    op.drop_index("ix_tenants_company_id", table_name="tenants")
    op.drop_table("tenants")
