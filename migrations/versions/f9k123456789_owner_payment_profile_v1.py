"""owner_payment_profile_v1

Revision ID: f9k123456789
Revises: f9j012345678
Create Date: 2026-07-14 16:00:00.000000

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f9k123456789"
down_revision: Union[str, None] = "f9j012345678"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_PROFILE_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")


def upgrade() -> None:
    op.create_table(
        "owner_payment_profile_v1",
        sa.Column("profile_key", sa.String(length=50), nullable=False),
        sa.Column("card_holder_name", sa.String(length=255), nullable=True),
        sa.Column("card_mask", sa.String(length=64), nullable=True),
        sa.Column("iban", sa.String(length=64), nullable=True),
        sa.Column("usdt_trc20_wallet", sa.String(length=128), nullable=True),
        sa.Column("usdt_erc20_wallet", sa.String(length=128), nullable=True),
        sa.Column("cash_instructions", sa.Text(), nullable=True),
        sa.Column("card_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("iban_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("usdt_trc20_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("usdt_erc20_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("cash_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("default_payment_method", sa.String(length=50), nullable=True),
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
        sa.UniqueConstraint("profile_key", name="uq_owner_payment_profile_v1_key"),
    )

    profile_table = sa.table(
        "owner_payment_profile_v1",
        sa.column("id", sa.UUID()),
        sa.column("profile_key", sa.String()),
        sa.column("card_holder_name", sa.String()),
        sa.column("card_mask", sa.String()),
        sa.column("iban", sa.String()),
        sa.column("usdt_trc20_wallet", sa.String()),
        sa.column("usdt_erc20_wallet", sa.String()),
        sa.column("cash_instructions", sa.Text()),
        sa.column("card_enabled", sa.Boolean()),
        sa.column("iban_enabled", sa.Boolean()),
        sa.column("usdt_trc20_enabled", sa.Boolean()),
        sa.column("usdt_erc20_enabled", sa.Boolean()),
        sa.column("cash_enabled", sa.Boolean()),
        sa.column("default_payment_method", sa.String()),
    )
    op.bulk_insert(
        profile_table,
        [
            {
                "id": DEFAULT_PROFILE_ID,
                "profile_key": "default",
                "card_holder_name": "Platform Services LLC",
                "card_mask": "**** **** **** 0000",
                "iban": "UA21322313000002600723356601",
                "usdt_trc20_wallet": "TXYZplatformWalletTRC20Example",
                "usdt_erc20_wallet": "0xPlatformWalletERC20Example",
                "cash_instructions": "Офис: Киев, ул. Примерная 1\nЧасы: Пн–Пт 10:00–18:00",
                "card_enabled": True,
                "iban_enabled": True,
                "usdt_trc20_enabled": True,
                "usdt_erc20_enabled": True,
                "cash_enabled": True,
                "default_payment_method": "CARD",
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("owner_payment_profile_v1")
