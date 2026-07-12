"""multi_company_engine_v1

Revision ID: c4f1e8b23a01
Revises: 6a2a99ff8267
Create Date: 2026-07-12 23:36:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c4f1e8b23a01"
down_revision: Union[str, None] = "6a2a99ff8267"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "multi_company_v1_companies",
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("legal_name", sa.String(length=300), nullable=False),
        sa.Column("tax_id", sa.String(length=50), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("country", sa.String(length=50), nullable=True),
        sa.Column("accounting_prefix", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.UniqueConstraint("code", name="uq_multi_company_v1_companies_code"),
    )
    op.create_index(
        "ix_multi_company_v1_companies_is_active",
        "multi_company_v1_companies",
        ["is_active"],
        unique=False,
    )
    op.create_table(
        "multi_company_v1_consolidated_reports",
        sa.Column("report_type", sa.String(length=30), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("companies_included", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("generated_by", sa.BigInteger(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_multi_company_v1_cr_period",
        "multi_company_v1_consolidated_reports",
        ["period_start", "period_end"],
        unique=False,
    )
    op.create_index(
        "ix_multi_company_v1_cr_status",
        "multi_company_v1_consolidated_reports",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_multi_company_v1_cr_type",
        "multi_company_v1_consolidated_reports",
        ["report_type"],
        unique=False,
    )
    op.create_table(
        "multi_company_v1_branches",
        sa.Column("company_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("country", sa.String(length=50), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("shared_inventory", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "code",
            name="uq_multi_company_v1_branches_company_code",
        ),
    )
    op.create_index(
        "ix_multi_company_v1_branches_company",
        "multi_company_v1_branches",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_multi_company_v1_branches_region",
        "multi_company_v1_branches",
        ["region"],
        unique=False,
    )
    op.create_table(
        "multi_company_v1_intercompany_transactions",
        sa.Column("from_company_id", sa.UUID(), nullable=False),
        sa.Column("to_company_id", sa.UUID(), nullable=False),
        sa.Column("from_branch_id", sa.UUID(), nullable=True),
        sa.Column("to_branch_id", sa.UUID(), nullable=True),
        sa.Column("transaction_type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("vehicle_id", sa.UUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
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
        sa.CheckConstraint("amount >= 0", name="ck_multi_company_v1_ict_amount"),
        sa.ForeignKeyConstraint(
            ["from_branch_id"],
            ["multi_company_v1_branches.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["from_company_id"],
            ["multi_company_v1_companies.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["to_branch_id"],
            ["multi_company_v1_branches.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["to_company_id"],
            ["multi_company_v1_companies.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["automotive_v1_vehicles.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_multi_company_v1_ict_from_company",
        "multi_company_v1_intercompany_transactions",
        ["from_company_id"],
        unique=False,
    )
    op.create_index(
        "ix_multi_company_v1_ict_reference",
        "multi_company_v1_intercompany_transactions",
        ["reference"],
        unique=False,
    )
    op.create_index(
        "ix_multi_company_v1_ict_status",
        "multi_company_v1_intercompany_transactions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_multi_company_v1_ict_to_company",
        "multi_company_v1_intercompany_transactions",
        ["to_company_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_multi_company_v1_ict_to_company",
        table_name="multi_company_v1_intercompany_transactions",
    )
    op.drop_index(
        "ix_multi_company_v1_ict_status",
        table_name="multi_company_v1_intercompany_transactions",
    )
    op.drop_index(
        "ix_multi_company_v1_ict_reference",
        table_name="multi_company_v1_intercompany_transactions",
    )
    op.drop_index(
        "ix_multi_company_v1_ict_from_company",
        table_name="multi_company_v1_intercompany_transactions",
    )
    op.drop_table("multi_company_v1_intercompany_transactions")
    op.drop_index(
        "ix_multi_company_v1_branches_region",
        table_name="multi_company_v1_branches",
    )
    op.drop_index(
        "ix_multi_company_v1_branches_company",
        table_name="multi_company_v1_branches",
    )
    op.drop_table("multi_company_v1_branches")
    op.drop_index(
        "ix_multi_company_v1_cr_type",
        table_name="multi_company_v1_consolidated_reports",
    )
    op.drop_index(
        "ix_multi_company_v1_cr_status",
        table_name="multi_company_v1_consolidated_reports",
    )
    op.drop_index(
        "ix_multi_company_v1_cr_period",
        table_name="multi_company_v1_consolidated_reports",
    )
    op.drop_table("multi_company_v1_consolidated_reports")
    op.drop_index(
        "ix_multi_company_v1_companies_is_active",
        table_name="multi_company_v1_companies",
    )
    op.drop_table("multi_company_v1_companies")
