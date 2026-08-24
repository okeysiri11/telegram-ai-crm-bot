"""FX market intelligence persistence models — Sprint 50.1.

Canonical tables for market snapshots, analysis runs, agent outputs,
consensus, signals, news, macro events, and evaluation outcomes.
Tenant-scoped for user-generated analyses; news/macro may be cached globally
(tenant_id nullable / 'global').
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class FxMarketSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "fx_mi_market_snapshots"
    __table_args__ = (
        Index("ix_fx_mi_snap_tenant_symbol", "tenant_id", "symbol"),
        Index("ix_fx_mi_snap_fetched", "fetched_at"),
    )

    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="global")
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str | None] = mapped_column(String(16), nullable=True)
    mid: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bid: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ask: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class FxAnalysisRun(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "fx_mi_analysis_runs"
    __table_args__ = (
        Index("ix_fx_mi_run_tenant_created", "tenant_id", "created_at"),
        Index("ix_fx_mi_run_instrument", "instrument"),
        Index("ix_fx_mi_run_preset", "preset_id"),
    )

    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    preset_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    analysis_type: Mapped[str] = mapped_column(String(64), nullable=False, default="full")
    instrument: Mapped[str] = mapped_column(String(32), nullable=False, default="EUR/USD")
    direction: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_at_analysis: Mapped[str | None] = mapped_column(String(32), nullable=True)
    dxy_at_analysis: Mapped[str | None] = mapped_column(String(32), nullable=True)
    market_regime: Mapped[str | None] = mapped_column(String(64), nullable=True)
    missing_sources: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    snapshot_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")


class FxAgentOutput(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "fx_mi_agent_outputs"
    __table_args__ = (Index("ix_fx_mi_agent_run", "analysis_run_id"),)

    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    analysis_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vote: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class FxConsensusRun(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "fx_mi_consensus_runs"
    __table_args__ = (Index("ix_fx_mi_consensus_run", "analysis_run_id"),)

    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    analysis_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    overall_direction: Mapped[str | None] = mapped_column(String(32), nullable=True)
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    disagreement_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class FxSignalRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "fx_mi_signals"
    __table_args__ = (
        Index("ix_fx_mi_signal_tenant", "tenant_id", "created_at"),
        Index("ix_fx_mi_signal_run", "analysis_run_id"),
    )

    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    analysis_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    signal_key: Mapped[str] = mapped_column(String(64), nullable=False)
    instrument: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str | None] = mapped_column(String(16), nullable=True)
    signal: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_at_signal: Mapped[str | None] = mapped_column(String(32), nullable=True)
    entry_zone: Mapped[str | None] = mapped_column(String(128), nullable=True)
    invalidation: Mapped[str | None] = mapped_column(Text, nullable=True)
    reasons: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="NO_SIGNAL")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    analytics_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    trade_execution: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class FxNewsItem(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "fx_mi_news_items"
    __table_args__ = (
        UniqueConstraint("duplicate_group_id", name="uq_fx_mi_news_dedupe"),
        Index("ix_fx_mi_news_published", "published_at"),
    )

    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="global")
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    instruments: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    topics: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    importance: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ai_assessment: Mapped[str | None] = mapped_column(String(128), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    duplicate_group_id: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class FxMacroEvent(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "fx_mi_macro_events"
    __table_args__ = (
        Index("ix_fx_mi_macro_scheduled", "scheduled_at"),
        Index("ix_fx_mi_macro_event", "event"),
    )

    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="global")
    event: Mapped[str] = mapped_column(String(64), nullable=False)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual: Mapped[str | None] = mapped_column(String(64), nullable=True)
    forecast: Mapped[str | None] = mapped_column(String(64), nullable=True)
    previous: Mapped[str | None] = mapped_column(String(64), nullable=True)
    importance: Mapped[str | None] = mapped_column(String(32), nullable=True)
    affected_instruments: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduled")
    external_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class FxAnalysisEvaluation(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "fx_mi_analysis_evaluations"
    __table_args__ = (
        UniqueConstraint("analysis_run_id", "horizon", name="uq_fx_mi_eval_run_horizon"),
        Index("ix_fx_mi_eval_status", "evaluation_status"),
    )

    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    analysis_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    instrument: Mapped[str] = mapped_column(String(32), nullable=False, default="EUR/USD")
    horizon: Mapped[str] = mapped_column(String(16), nullable=False)
    price_at_analysis: Mapped[str | None] = mapped_column(String(32), nullable=True)
    price_after: Mapped[str | None] = mapped_column(String(32), nullable=True)
    actual_move: Mapped[float | None] = mapped_column(Float, nullable=True)
    direction_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    signal_outcome: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mfe: Mapped[float | None] = mapped_column(Float, nullable=True)
    mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    evaluation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)



class FxPaperOrder(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "fx_mi_paper_orders"
    __table_args__ = (Index("ix_fx_mi_paper_orders_tenant", "tenant_id", "created_at"),)

    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    order_key: Mapped[str] = mapped_column(String(64), nullable=False)
    instrument: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    order_type: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    limit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    fill_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    analysis_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class FxPaperPosition(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "fx_mi_paper_positions"
    __table_args__ = (Index("ix_fx_mi_paper_pos_tenant", "tenant_id", "status"),)

    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    position_key: Mapped[str] = mapped_column(String(64), nullable=False)
    order_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    instrument: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    analysis_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class FxJournalEntry(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "fx_mi_journal_entries"
    __table_args__ = (Index("ix_fx_mi_journal_tenant", "tenant_id", "created_at"),)

    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    journal_key: Mapped[str] = mapped_column(String(64), nullable=False)
    instrument: Mapped[str | None] = mapped_column(String(32), nullable=True)
    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    signal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    analysis_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
