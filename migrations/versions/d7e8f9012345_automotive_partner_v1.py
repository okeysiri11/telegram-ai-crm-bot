"""automotive_partner_v1

Revision ID: d7e8f9012345
Revises: c6d7e8901234
Create Date: 2026-07-13 22:00:00.000000

Ensures automotive_partner_v1_partners exists with logo_url and seeds core partners.
"""
from __future__ import annotations

import json
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d7e8f9012345"
down_revision: Union[str, None] = "c6d7e8901234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "automotive_partner_v1_partners"

SEED_PARTNERS = (
    ("sgtas", "SG TAS", "INSURANCE", "https://sgtas.ua", None, None),
    ("arx", "ARX", "INSURANCE", "https://arx.com.ua", None, None),
    ("uniqa", "UNIQA", "INSURANCE", "https://uniqa.ua", None, None),
    ("privatbank", "PrivatBank", "CREDIT", "https://privatbank.ua", None, None),
    ("oschadbank", "Oschadbank", "CREDIT", "https://oschadbank.ua", None, None),
    ("otp_leasing", "OTP Leasing", "LEASING", "https://otpleasing.ua", None, None),
    ("ulf_finance", "ULF Finance", "LEASING", "https://ulffinance.ua", None, None),
    ("tas_leasing", "TAS Leasing", "LEASING", "https://tasleasing.ua", None, None),
    ("nmt_global", "NMT Global", "LOGISTICS", "https://nmtglobal.ua", None, None),
    ("autologistika", "Autologistika", "LOGISTICS", "https://autologistika.ua", None, None),
    (
        "default_legal_partner",
        "Default Legal Partner",
        "LEGAL",
        None,
        None,
        None,
    ),
)


def _table_exists(conn, table_name: str) -> bool:
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def _column_names(conn, table_name: str) -> set[str]:
    inspector = sa.inspect(conn)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _ensure_partners_table(conn) -> None:
    if _table_exists(conn, TABLE):
        columns = _column_names(conn, TABLE)
        if "logo_url" not in columns:
            op.add_column(TABLE, sa.Column("logo_url", sa.Text(), nullable=True))
        return

    op.create_table(
        TABLE,
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("partner_type", sa.String(length=64), nullable=False),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("telegram_channel", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column(
            "tenant_mode_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
        ),
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
        sa.UniqueConstraint("code", name="uq_automotive_partner_v1_partners_code"),
    )
    op.create_index("ix_automotive_partner_v1_partners_type", TABLE, ["partner_type"])
    op.create_index("ix_automotive_partner_v1_partners_active", TABLE, ["is_active"])


def _seed_partners(conn) -> None:
    for code, name, partner_type, website, telegram_channel, logo_url in SEED_PARTNERS:
        partner_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                f"""
                INSERT INTO {TABLE}
                (
                    id, code, name, partner_type, website, telegram_channel, logo_url,
                    tenant_mode_enabled, is_active, metadata, created_at, updated_at
                )
                VALUES
                (
                    :id, :code, :name, :partner_type, :website, :telegram_channel, :logo_url,
                    false, true, :metadata, NOW(), NOW()
                )
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    partner_type = EXCLUDED.partner_type,
                    website = COALESCE(EXCLUDED.website, {TABLE}.website),
                    telegram_channel = COALESCE(EXCLUDED.telegram_channel, {TABLE}.telegram_channel),
                    logo_url = COALESCE(EXCLUDED.logo_url, {TABLE}.logo_url),
                    is_active = true,
                    updated_at = NOW()
                """
            ),
            {
                "id": partner_id,
                "code": code,
                "name": name,
                "partner_type": partner_type,
                "website": website,
                "telegram_channel": telegram_channel,
                "logo_url": logo_url,
                "metadata": json.dumps({"seed": "automotive_partner_v1"}),
            },
        )


def upgrade() -> None:
    conn = op.get_bind()
    _ensure_partners_table(conn)
    _seed_partners(conn)


def downgrade() -> None:
    conn = op.get_bind()
    codes = ", ".join(f"'{code}'" for code, *_ in SEED_PARTNERS)
    conn.execute(
        sa.text(
            f"DELETE FROM {TABLE} WHERE code IN ({codes})"
        )
    )
