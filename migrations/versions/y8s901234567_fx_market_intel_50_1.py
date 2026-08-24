"""FX market intelligence persistence — Sprint 50.1.

Revision ID: y8s901234567
Revises: x7r890123456
Create Date: 2026-08-11 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "y8s901234567"
down_revision: Union[str, None] = "x7r890123456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts_cols():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("change_id", sa.String(length=64), nullable=True),
        sa.Column("source_client", sa.String(length=32), nullable=True),
        sa.Column("workspace_id", sa.String(length=128), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", JSONB(), nullable=True),
    ]


def upgrade() -> None:
    conn = op.get_bind()

    def _exists(name: str) -> bool:
        row = conn.exec_driver_sql(f"SELECT to_regclass('public.{name}')").scalar()
        return row is not None

    if _exists("fx_mi_market_snapshots"):
        return

    op.create_table(
        "fx_mi_market_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False, server_default="global"),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(16), nullable=True),
        sa.Column("mid", sa.String(32), nullable=True),
        sa.Column("bid", sa.String(32), nullable=True),
        sa.Column("ask", sa.String(32), nullable=True),
        sa.Column("source", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", JSONB(), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_fx_mi_snap_tenant_symbol", "fx_mi_market_snapshots", ["tenant_id", "symbol"])
    op.create_index("ix_fx_mi_snap_fetched", "fx_mi_market_snapshots", ["fetched_at"])

    op.create_table(
        "fx_mi_analysis_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
        sa.Column("user_id", sa.String(128), nullable=True),
        sa.Column("preset_id", sa.String(64), nullable=True),
        sa.Column("analysis_type", sa.String(64), nullable=False, server_default="full"),
        sa.Column("instrument", sa.String(32), nullable=False, server_default="EUR/USD"),
        sa.Column("direction", sa.String(32), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("price_at_analysis", sa.String(32), nullable=True),
        sa.Column("dxy_at_analysis", sa.String(32), nullable=True),
        sa.Column("market_regime", sa.String(64), nullable=True),
        sa.Column("missing_sources", JSONB(), nullable=True),
        sa.Column("snapshot_id", sa.String(64), nullable=True),
        sa.Column("payload", JSONB(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="completed"),
        *_ts_cols(),
    )
    op.create_index("ix_fx_mi_run_tenant_created", "fx_mi_analysis_runs", ["tenant_id", "created_at"])
    op.create_index("ix_fx_mi_run_instrument", "fx_mi_analysis_runs", ["instrument"])
    op.create_index("ix_fx_mi_run_preset", "fx_mi_analysis_runs", ["preset_id"])

    op.create_table(
        "fx_mi_agent_outputs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
        sa.Column("analysis_run_id", sa.String(64), nullable=False),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("agent_name", sa.String(128), nullable=True),
        sa.Column("vote", sa.String(32), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("payload", JSONB(), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_fx_mi_agent_run", "fx_mi_agent_outputs", ["analysis_run_id"])

    op.create_table(
        "fx_mi_consensus_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
        sa.Column("analysis_run_id", sa.String(64), nullable=False),
        sa.Column("overall_direction", sa.String(32), nullable=True),
        sa.Column("overall_confidence", sa.Float(), nullable=True),
        sa.Column("disagreement_score", sa.Float(), nullable=True),
        sa.Column("payload", JSONB(), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_fx_mi_consensus_run", "fx_mi_consensus_runs", ["analysis_run_id"])

    op.create_table(
        "fx_mi_signals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
        sa.Column("analysis_run_id", sa.String(64), nullable=True),
        sa.Column("signal_key", sa.String(64), nullable=False),
        sa.Column("instrument", sa.String(32), nullable=False),
        sa.Column("timeframe", sa.String(16), nullable=True),
        sa.Column("signal", sa.String(32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("price_at_signal", sa.String(32), nullable=True),
        sa.Column("entry_zone", sa.String(128), nullable=True),
        sa.Column("invalidation", sa.Text(), nullable=True),
        sa.Column("reasons", JSONB(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="NO_SIGNAL"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("analytics_only", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("trade_execution", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload", JSONB(), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_fx_mi_signal_tenant", "fx_mi_signals", ["tenant_id", "created_at"])
    op.create_index("ix_fx_mi_signal_run", "fx_mi_signals", ["analysis_run_id"])

    op.create_table(
        "fx_mi_news_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False, server_default="global"),
        sa.Column("source", sa.String(128), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("url", sa.String(1024), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("region", sa.String(64), nullable=True),
        sa.Column("instruments", JSONB(), nullable=True),
        sa.Column("topics", JSONB(), nullable=True),
        sa.Column("importance", sa.String(32), nullable=True),
        sa.Column("sentiment", sa.String(64), nullable=True),
        sa.Column("ai_assessment", sa.String(128), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("duplicate_group_id", sa.String(64), nullable=False),
        sa.Column("payload", JSONB(), nullable=True),
        *_ts_cols(),
        sa.UniqueConstraint("duplicate_group_id", name="uq_fx_mi_news_dedupe"),
    )
    op.create_index("ix_fx_mi_news_published", "fx_mi_news_items", ["published_at"])

    op.create_table(
        "fx_mi_macro_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False, server_default="global"),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column("country", sa.String(64), nullable=True),
        sa.Column("region", sa.String(64), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual", sa.String(64), nullable=True),
        sa.Column("forecast", sa.String(64), nullable=True),
        sa.Column("previous", sa.String(64), nullable=True),
        sa.Column("importance", sa.String(32), nullable=True),
        sa.Column("affected_instruments", JSONB(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="scheduled"),
        sa.Column("external_key", sa.String(256), nullable=True),
        sa.Column("payload", JSONB(), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_fx_mi_macro_scheduled", "fx_mi_macro_events", ["scheduled_at"])
    op.create_index("ix_fx_mi_macro_event", "fx_mi_macro_events", ["event"])

    op.create_table(
        "fx_mi_analysis_evaluations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(128), nullable=False, server_default="default"),
        sa.Column("analysis_run_id", sa.String(64), nullable=False),
        sa.Column("instrument", sa.String(32), nullable=False, server_default="EUR/USD"),
        sa.Column("horizon", sa.String(16), nullable=False),
        sa.Column("price_at_analysis", sa.String(32), nullable=True),
        sa.Column("price_after", sa.String(32), nullable=True),
        sa.Column("actual_move", sa.Float(), nullable=True),
        sa.Column("direction_correct", sa.Boolean(), nullable=True),
        sa.Column("signal_outcome", sa.String(64), nullable=True),
        sa.Column("mfe", sa.Float(), nullable=True),
        sa.Column("mae", sa.Float(), nullable=True),
        sa.Column("evaluation_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("payload", JSONB(), nullable=True),
        *_ts_cols(),
        sa.UniqueConstraint("analysis_run_id", "horizon", name="uq_fx_mi_eval_run_horizon"),
    )
    op.create_index("ix_fx_mi_eval_status", "fx_mi_analysis_evaluations", ["evaluation_status"])


def downgrade() -> None:
    # Non-destructive: leave tables in place (repo policy).
    pass
