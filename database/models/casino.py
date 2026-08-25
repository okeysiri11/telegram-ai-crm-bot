# Casino play-money foundation — PostgreSQL models (Sprint 15).

from __future__ import annotations

from sqlalchemy import Boolean, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin


class CasinoVenueRow(TimestampMixin, Base):
    __tablename__ = "casino_venues"
    __table_args__ = (
        Index("ix_casino_venues_tenant", "tenant_id"),
        UniqueConstraint("tenant_id", "slug", name="uq_casino_venues_tenant_slug"),
    )

    venue_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, server_default="default")
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city_building_id: Mapped[str] = mapped_column(String(64), nullable=False, server_default="casino")
    city_route: Mapped[str] = mapped_column(String(255), nullable=False)
    game: Mapped[str] = mapped_column(String(64), nullable=False, server_default="roulette")
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="open")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class CasinoWalletRow(TimestampMixin, Base):
    __tablename__ = "casino_wallets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "player_id", name="uq_casino_wallets_tenant_player"),
        Index("ix_casino_wallets_tenant", "tenant_id"),
    )

    wallet_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, server_default="default")
    player_id: Mapped[str] = mapped_column(String(64), nullable=False)
    balance_chips: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    currency_code: Mapped[str] = mapped_column(String(16), nullable=False, server_default="CHIPS")


class CasinoLedgerRow(TimestampMixin, Base):
    __tablename__ = "casino_ledger"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_casino_ledger_tenant_idempotency"),
        Index("ix_casino_ledger_tenant_player", "tenant_id", "player_id"),
        Index("ix_casino_ledger_reference", "tenant_id", "reference_type", "reference_id"),
    )

    entry_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, server_default="default")
    player_id: Mapped[str] = mapped_column(String(64), nullable=False)
    wallet_id: Mapped[str] = mapped_column(String(64), nullable=False)
    amount_chips: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(64), nullable=False, server_default="")
    reference_id: Mapped[str] = mapped_column(String(64), nullable=False, server_default="")
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_ts: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    note: Mapped[str] = mapped_column(Text, nullable=False, server_default="")


class CasinoRouletteRoundRow(TimestampMixin, Base):
    __tablename__ = "casino_roulette_rounds"
    __table_args__ = (Index("ix_casino_rounds_tenant_venue", "tenant_id", "venue_id"),)

    round_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, server_default="default")
    venue_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="open")
    result_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    entropy_hex: Mapped[str] = mapped_column(String(64), nullable=False, server_default="")
    settled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class CasinoRouletteBetRow(TimestampMixin, Base):
    __tablename__ = "casino_roulette_bets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_casino_bets_tenant_idempotency"),
        Index("ix_casino_bets_round", "tenant_id", "round_id"),
    )

    bet_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, server_default="default")
    player_id: Mapped[str] = mapped_column(String(64), nullable=False)
    round_id: Mapped[str] = mapped_column(String(64), nullable=False)
    bet_type: Mapped[str] = mapped_column(String(32), nullable=False)
    numbers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    amount_chips: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="accepted")
    payout_chips: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
