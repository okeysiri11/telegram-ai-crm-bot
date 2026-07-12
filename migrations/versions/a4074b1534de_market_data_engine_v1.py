"""market_data_engine_v1

Revision ID: a4074b1534de
Revises: bfdac8a7c0bd
Create Date: 2026-07-12 18:19:29.370527

"""
from __future__ import annotations

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a4074b1534de"
down_revision: Union[str, None] = "bfdac8a7c0bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_EVENT_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("market.quote.updated", "Emit or subscribe to market quote updated events"),
    ("market.spread.changed", "Emit or subscribe to market spread changed events"),
    ("market.source.failed", "Emit or subscribe to market source failed events"),
)

NEW_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "MANAGER": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "ADMIN": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "OWNER": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
    "ACCOUNTANT": frozenset({code for code, _ in NEW_EVENT_PERMISSIONS}),
}

DEFAULT_SOURCES: tuple[tuple[str, str, str, str, int, dict | None], ...] = (
    (
        "BINANCE",
        "EXCHANGE",
        "Binance Spot",
        "https://api.binance.com",
        10,
        None,
    ),
    (
        "BYBIT",
        "EXCHANGE",
        "Bybit Spot",
        "https://api.bybit.com",
        20,
        None,
    ),
    (
        "WHITEBIT",
        "EXCHANGE",
        "WhiteBIT Spot",
        "https://whitebit.com",
        30,
        None,
    ),
    (
        "FX",
        "FX",
        "FX Reference Rates",
        None,
        40,
        {
            "rates": {
                "USD": {"bid": "1.0", "ask": "1.0", "last": "1.0", "volume_24h": "0"},
                "EUR": {"bid": "1.08", "ask": "1.09", "last": "1.085", "volume_24h": "0"},
                "AED": {"bid": "0.272", "ask": "0.273", "last": "0.2725", "volume_24h": "0"},
                "PLN": {"bid": "0.25", "ask": "0.251", "last": "0.2505", "volume_24h": "0"},
                "GEL": {"bid": "0.37", "ask": "0.371", "last": "0.3705", "volume_24h": "0"},
            }
        },
    ),
    (
        "MANUAL",
        "MANUAL",
        "Manual Rates",
        None,
        50,
        None,
    ),
    (
        "PRECIOUS_METALS",
        "METALS",
        "Precious Metals Reference",
        None,
        60,
        {
            "rates": {
                "XAU": {"bid": "2650", "ask": "2655", "last": "2652.5", "volume_24h": "0"},
                "XAG": {"bid": "31.2", "ask": "31.4", "last": "31.3", "volume_24h": "0"},
            }
        },
    ),
)


def _seed_market_event_permissions() -> None:
    bind = op.get_bind()
    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.String()),
        sa.column("description", sa.Text()),
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.UUID()),
        sa.column("permission_id", sa.UUID()),
    )

    permission_ids: dict[str, uuid.UUID] = {}
    for code, description in NEW_EVENT_PERMISSIONS:
        existing = bind.execute(
            sa.text("SELECT id FROM permissions WHERE code = :code"),
            {"code": code},
        ).first()
        if existing:
            permission_ids[code] = existing[0]
            continue
        permission_id = uuid.uuid4()
        bind.execute(
            permissions_table.insert().values(
                id=permission_id,
                code=code,
                description=description,
            )
        )
        permission_ids[code] = permission_id

    for role_code, permission_codes in NEW_ROLE_PERMISSIONS.items():
        role_row = bind.execute(
            sa.text("SELECT id FROM roles WHERE code = :code"),
            {"code": role_code},
        ).first()
        if not role_row:
            continue
        role_id = role_row[0]
        for permission_code in permission_codes:
            permission_id = permission_ids.get(permission_code)
            if permission_id is None:
                perm_row = bind.execute(
                    sa.text("SELECT id FROM permissions WHERE code = :code"),
                    {"code": permission_code},
                ).first()
                if not perm_row:
                    continue
                permission_id = perm_row[0]
            exists = bind.execute(
                sa.text(
                    "SELECT 1 FROM role_permissions "
                    "WHERE role_id = :role_id AND permission_id = :permission_id"
                ),
                {"role_id": role_id, "permission_id": permission_id},
            ).first()
            if exists:
                continue
            bind.execute(
                role_permissions_table.insert().values(
                    role_id=role_id,
                    permission_id=permission_id,
                )
            )


def _seed_market_sources() -> None:
    bind = op.get_bind()
    sources_table = sa.table(
        "market_v1_sources",
        sa.column("id", sa.UUID()),
        sa.column("source_code", sa.String()),
        sa.column("source_type", sa.String()),
        sa.column("name", sa.String()),
        sa.column("base_url", sa.String()),
        sa.column("priority", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
        sa.column("config", postgresql.JSONB()),
        sa.column("failure_count", sa.Integer()),
    )
    for source_code, source_type, name, base_url, priority, config in DEFAULT_SOURCES:
        exists = bind.execute(
            sa.text("SELECT 1 FROM market_v1_sources WHERE source_code = :code"),
            {"code": source_code},
        ).first()
        if exists:
            continue
        bind.execute(
            sources_table.insert().values(
                id=uuid.uuid4(),
                source_code=source_code,
                source_type=source_type,
                name=name,
                base_url=base_url,
                priority=priority,
                is_active=True,
                config=config,
                failure_count=0,
            )
        )


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "market_v1_sources",
        sa.Column("source_code", sa.String(length=30), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("base_url", sa.String(length=255), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False),
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
        sa.UniqueConstraint("source_code"),
    )
    op.create_index(
        "ix_market_v1_sources_is_active",
        "market_v1_sources",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_market_v1_sources_priority",
        "market_v1_sources",
        ["priority"],
        unique=False,
    )
    op.create_index(
        "ix_market_v1_sources_source_code",
        "market_v1_sources",
        ["source_code"],
        unique=False,
    )
    op.create_table(
        "market_v1_orderbooks",
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("asset", sa.String(length=20), nullable=False),
        sa.Column("bids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("asks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["market_v1_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_market_v1_orderbooks_asset",
        "market_v1_orderbooks",
        ["asset"],
        unique=False,
    )
    op.create_index(
        "ix_market_v1_orderbooks_captured_at",
        "market_v1_orderbooks",
        ["captured_at"],
        unique=False,
    )
    op.create_index(
        "ix_market_v1_orderbooks_source_id",
        "market_v1_orderbooks",
        ["source_id"],
        unique=False,
    )
    op.create_table(
        "market_v1_quotes",
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("asset", sa.String(length=20), nullable=False),
        sa.Column("quote_symbol", sa.String(length=40), nullable=True),
        sa.Column("bid", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("ask", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("last", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("spread", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("volume_24h", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column(
            "quoted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.CheckConstraint("ask >= 0", name="ck_market_v1_quotes_ask"),
        sa.CheckConstraint("bid >= 0", name="ck_market_v1_quotes_bid"),
        sa.CheckConstraint("last >= 0", name="ck_market_v1_quotes_last"),
        sa.ForeignKeyConstraint(["source_id"], ["market_v1_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "asset", name="uq_market_v1_quotes_source_asset"),
    )
    op.create_index("ix_market_v1_quotes_asset", "market_v1_quotes", ["asset"], unique=False)
    op.create_index(
        "ix_market_v1_quotes_quoted_at",
        "market_v1_quotes",
        ["quoted_at"],
        unique=False,
    )
    op.create_table(
        "market_v1_snapshots",
        sa.Column("snapshot_type", sa.String(length=20), nullable=False),
        sa.Column("asset", sa.String(length=20), nullable=True),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["source_id"], ["market_v1_sources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_market_v1_snapshots_asset",
        "market_v1_snapshots",
        ["asset"],
        unique=False,
    )
    op.create_index(
        "ix_market_v1_snapshots_captured_at",
        "market_v1_snapshots",
        ["captured_at"],
        unique=False,
    )
    op.create_index(
        "ix_market_v1_snapshots_snapshot_type",
        "market_v1_snapshots",
        ["snapshot_type"],
        unique=False,
    )
    op.create_table(
        "market_v1_spreads",
        sa.Column("asset", sa.String(length=20), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("best_bid", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("best_ask", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("mid_price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("spread_abs", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("spread_pct", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["market_v1_sources.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_v1_spreads_asset", "market_v1_spreads", ["asset"], unique=False)
    op.create_index(
        "ix_market_v1_spreads_calculated_at",
        "market_v1_spreads",
        ["calculated_at"],
        unique=False,
    )
    op.create_index(
        "ix_market_v1_spreads_source_id",
        "market_v1_spreads",
        ["source_id"],
        unique=False,
    )
    _seed_market_sources()
    _seed_market_event_permissions()
    # ### end Alembic commands ###


def downgrade() -> None:
    bind = op.get_bind()
    codes = [code for code, _ in NEW_EVENT_PERMISSIONS]
    bind.execute(
        sa.text(
            "DELETE FROM role_permissions "
            "WHERE permission_id IN (SELECT id FROM permissions WHERE code = ANY(:codes))"
        ),
        {"codes": codes},
    )
    bind.execute(
        sa.text("DELETE FROM permissions WHERE code = ANY(:codes)"),
        {"codes": codes},
    )
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_market_v1_spreads_source_id", table_name="market_v1_spreads")
    op.drop_index("ix_market_v1_spreads_calculated_at", table_name="market_v1_spreads")
    op.drop_index("ix_market_v1_spreads_asset", table_name="market_v1_spreads")
    op.drop_table("market_v1_spreads")
    op.drop_index("ix_market_v1_snapshots_snapshot_type", table_name="market_v1_snapshots")
    op.drop_index("ix_market_v1_snapshots_captured_at", table_name="market_v1_snapshots")
    op.drop_index("ix_market_v1_snapshots_asset", table_name="market_v1_snapshots")
    op.drop_table("market_v1_snapshots")
    op.drop_index("ix_market_v1_quotes_quoted_at", table_name="market_v1_quotes")
    op.drop_index("ix_market_v1_quotes_asset", table_name="market_v1_quotes")
    op.drop_table("market_v1_quotes")
    op.drop_index("ix_market_v1_orderbooks_source_id", table_name="market_v1_orderbooks")
    op.drop_index("ix_market_v1_orderbooks_captured_at", table_name="market_v1_orderbooks")
    op.drop_index("ix_market_v1_orderbooks_asset", table_name="market_v1_orderbooks")
    op.drop_table("market_v1_orderbooks")
    op.drop_index("ix_market_v1_sources_source_code", table_name="market_v1_sources")
    op.drop_index("ix_market_v1_sources_priority", table_name="market_v1_sources")
    op.drop_index("ix_market_v1_sources_is_active", table_name="market_v1_sources")
    op.drop_table("market_v1_sources")
    # ### end Alembic commands ###
