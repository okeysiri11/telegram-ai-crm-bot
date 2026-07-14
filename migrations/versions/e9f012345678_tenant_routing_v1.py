"""tenant_routing_v1

Revision ID: e9f012345678
Revises: d8e9f0123456
Create Date: 2026-07-14 11:00:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e9f012345678"
down_revision: Union[str, None] = "d8e9f0123456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED_LINKS = [
    ("auto_client", "auto_client", "auto", "🚗 Авто — клиент", "🚗 Авто — клієнт", "buyer", "hub_cars", 0),
    ("auto_dealer", "auto_dealer", "auto", "🏢 Авто — дилер", "🏢 Авто — дилер", "dealer", "hub_cars", 1),
    ("agro", "agro", "agro", "🌾 Agro Trading", "🌾 Agro Trading", None, None, 2),
    ("drones", "drones", "drones", "🚁 Drone Engineering", "🚁 Drone Engineering", None, None, 3),
    ("legal", "legal", "legal", "⚖ Юриспруденция", "⚖ Юриспруденция", None, None, 4),
    ("insurance_partner", "insurance_partner", "auto", "🛡 Страховой партнёр", "🛡 Страховий партнер", "insurance", "hub_insurance", 5),
    ("finance_partner", "finance_partner", "auto", "🏦 Финансовый партнёр", "🏦 Финансовий партнер", "bank", "hub_credit", 6),
    ("service_partner", "service_partner", "auto", "🔧 Сервисный партнёр", "🔧 Сервісний партнер", "service_station", "hub_cars", 7),
]


def upgrade() -> None:
    op.add_column(
        "user_vertical_preferences_v1",
        sa.Column("tenant_code", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "user_vertical_preferences_v1",
        sa.Column("source_link", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_user_vertical_prefs_tenant",
        "user_vertical_preferences_v1",
        ["tenant_code"],
    )
    op.create_index(
        "ix_user_vertical_prefs_source_link",
        "user_vertical_preferences_v1",
        ["source_link"],
    )

    op.create_table(
        "tenant_entry_links_v1",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("tenant_code", sa.String(length=64), nullable=False),
        sa.Column("vertical", sa.String(length=32), nullable=False),
        sa.Column("title_ru", sa.String(length=128), nullable=False),
        sa.Column("title_uk", sa.String(length=128), nullable=False),
        sa.Column("preset_role", sa.String(length=64), nullable=True),
        sa.Column("entry_target", sa.String(length=64), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_tenant_entry_links_code", "tenant_entry_links_v1", ["code"], unique=True)
    op.create_index("ix_tenant_entry_links_tenant", "tenant_entry_links_v1", ["tenant_code"])
    op.create_index("ix_tenant_entry_links_active", "tenant_entry_links_v1", ["is_active"])

    op.create_table(
        "owner_vertical_notes_v1",
        sa.Column("tenant_code", sa.String(length=64), nullable=False),
        sa.Column("vertical", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
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
    op.create_index("ix_owner_notes_vertical", "owner_vertical_notes_v1", ["vertical"])
    op.create_index("ix_owner_notes_tenant", "owner_vertical_notes_v1", ["tenant_code"])

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
            for code, tenant, vertical, title_ru, title_uk, role, target, sort_order in SEED_LINKS
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_owner_notes_tenant", table_name="owner_vertical_notes_v1")
    op.drop_index("ix_owner_notes_vertical", table_name="owner_vertical_notes_v1")
    op.drop_table("owner_vertical_notes_v1")
    op.drop_index("ix_tenant_entry_links_active", table_name="tenant_entry_links_v1")
    op.drop_index("ix_tenant_entry_links_tenant", table_name="tenant_entry_links_v1")
    op.drop_index("ix_tenant_entry_links_code", table_name="tenant_entry_links_v1")
    op.drop_table("tenant_entry_links_v1")
    op.drop_index("ix_user_vertical_prefs_source_link", table_name="user_vertical_preferences_v1")
    op.drop_index("ix_user_vertical_prefs_tenant", table_name="user_vertical_preferences_v1")
    op.drop_column("user_vertical_preferences_v1", "source_link")
    op.drop_column("user_vertical_preferences_v1", "tenant_code")
