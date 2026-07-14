"""lead_engine_v1

Revision ID: f0a123456789
Revises: e9f012345678
Create Date: 2026-07-14 12:00:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f0a123456789"
down_revision: Union[str, None] = "e9f012345678"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXTRA_ENTRY_LINKS = [
    ("agro_farmer", "agro_farmer", "agro", "🌾 Agro — фермер", "🌾 Agro — фермер", "farmer", None, 8),
    ("agro_supplier", "agro_supplier", "agro", "🌾 Agro — поставщик", "🌾 Agro — постачальник", "supplier", None, 9),
]


def upgrade() -> None:
    op.create_table(
        "lead_engine_v1_leads",
        sa.Column("vertical", sa.String(length=50), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=True),
        sa.Column("language", sa.String(length=8), nullable=True),
        sa.Column("source_link", sa.String(length=255), nullable=True),
        sa.Column("utm_source", sa.String(length=255), nullable=True),
        sa.Column("utm_campaign", sa.String(length=255), nullable=True),
        sa.Column("utm_medium", sa.String(length=255), nullable=True),
        sa.Column("referral_code", sa.String(length=255), nullable=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("telegram_username", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("assigned_manager_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="NEW"),
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
        sa.ForeignKeyConstraint(["assigned_manager_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lead_engine_v1_vertical", "lead_engine_v1_leads", ["vertical"])
    op.create_index("ix_lead_engine_v1_status", "lead_engine_v1_leads", ["status"])
    op.create_index("ix_lead_engine_v1_source_link", "lead_engine_v1_leads", ["source_link"])
    op.create_index("ix_lead_engine_v1_telegram", "lead_engine_v1_leads", ["telegram_user_id"])
    op.create_index("ix_lead_engine_v1_manager", "lead_engine_v1_leads", ["assigned_manager_id"])
    op.create_index("ix_lead_engine_v1_created", "lead_engine_v1_leads", ["created_at"])
    op.create_index("ix_lead_engine_v1_utm_source", "lead_engine_v1_leads", ["utm_source"])

    links_table = sa.table(
        "tenant_entry_links_v1",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.String()),
        sa.column("tenant_code", sa.String()),
        sa.column("vertical", sa.String()),
        sa.column("title_ru", sa.String()),
        sa.column("title_uk", sa.String()),
        sa.column("preset_role", sa.String()),
        sa.column("entry_target", sa.String()),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        links_table,
        [
            {
                "id": uuid.uuid4(),
                "code": code,
                "tenant_code": tenant,
                "vertical": vertical,
                "title_ru": title_ru,
                "title_uk": title_uk,
                "preset_role": role,
                "entry_target": target,
                "sort_order": sort_order,
                "is_active": True,
            }
            for code, tenant, vertical, title_ru, title_uk, role, target, sort_order in EXTRA_ENTRY_LINKS
        ],
    )


def downgrade() -> None:
    for code, *_ in EXTRA_ENTRY_LINKS:
        op.execute(
            sa.text("DELETE FROM tenant_entry_links_v1 WHERE code = :code").bindparams(code=code)
        )
    op.drop_index("ix_lead_engine_v1_utm_source", table_name="lead_engine_v1_leads")
    op.drop_index("ix_lead_engine_v1_created", table_name="lead_engine_v1_leads")
    op.drop_index("ix_lead_engine_v1_manager", table_name="lead_engine_v1_leads")
    op.drop_index("ix_lead_engine_v1_telegram", table_name="lead_engine_v1_leads")
    op.drop_index("ix_lead_engine_v1_source_link", table_name="lead_engine_v1_leads")
    op.drop_index("ix_lead_engine_v1_status", table_name="lead_engine_v1_leads")
    op.drop_index("ix_lead_engine_v1_vertical", table_name="lead_engine_v1_leads")
    op.drop_table("lead_engine_v1_leads")
