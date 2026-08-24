# FX market intelligence repository — Sprint 50.1.
#
# AsyncSession + flush-based writes; news upsert relies on DB UniqueConstraint
# on duplicate_group_id with IntegrityError recovery for concurrent inserts.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.fx_market_intel import (
    FxAgentOutput,
    FxAnalysisEvaluation,
    FxAnalysisRun,
    FxConsensusRun,
    FxJournalEntry,
    FxMacroEvent,
    FxMarketSnapshot,
    FxNewsItem,
    FxPaperOrder,
    FxPaperPosition,
    FxSignalRow,
)

_EVALUATION_HORIZONS = ("1h", "4h", "1d")


class FxMarketIntelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_snapshot(self, **fields) -> FxMarketSnapshot:
        row = FxMarketSnapshot(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def save_analysis_run(self, **fields) -> FxAnalysisRun:
        row = FxAnalysisRun(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def save_agent_output(self, **fields) -> FxAgentOutput:
        row = FxAgentOutput(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def save_consensus(self, **fields) -> FxConsensusRun:
        row = FxConsensusRun(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def save_signal(self, **fields) -> FxSignalRow:
        row = FxSignalRow(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def _get_news_by_duplicate_group_id(
        self, duplicate_group_id: str
    ) -> FxNewsItem | None:
        result = await self._session.execute(
            select(FxNewsItem).where(FxNewsItem.duplicate_group_id == duplicate_group_id)
        )
        return result.scalar_one_or_none()

    async def upsert_news(self, item: dict[str, Any]) -> FxNewsItem:
        duplicate_group_id = item["duplicate_group_id"]
        existing = await self._get_news_by_duplicate_group_id(duplicate_group_id)
        if existing is not None:
            return existing

        row = FxNewsItem(**item)
        self._session.add(row)
        try:
            async with self._session.begin_nested():
                await self._session.flush()
            return row
        except IntegrityError:
            existing = await self._get_news_by_duplicate_group_id(duplicate_group_id)
            if existing is not None:
                return existing
            raise

    async def _get_macro_by_external_key(self, external_key: str) -> FxMacroEvent | None:
        result = await self._session.execute(
            select(FxMacroEvent).where(FxMacroEvent.external_key == external_key)
        )
        return result.scalar_one_or_none()

    async def upsert_macro(self, event: dict[str, Any]) -> FxMacroEvent:
        external_key = event.get("external_key")
        if external_key:
            existing = await self._get_macro_by_external_key(external_key)
            if existing is not None:
                return existing

        row = FxMacroEvent(**event)
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_analysis_runs(
        self, tenant_id: str, *, limit: int = 50
    ) -> list[FxAnalysisRun]:
        result = await self._session.execute(
            select(FxAnalysisRun)
            .where(FxAnalysisRun.tenant_id == tenant_id)
            .order_by(FxAnalysisRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_analysis_run(self, run_id: str) -> FxAnalysisRun | None:
        parsed = uuid.UUID(run_id)
        result = await self._session.execute(
            select(FxAnalysisRun).where(FxAnalysisRun.id == parsed)
        )
        return result.scalar_one_or_none()

    async def list_agent_outputs(self, analysis_run_id: str) -> list[FxAgentOutput]:
        result = await self._session.execute(
            select(FxAgentOutput)
            .where(FxAgentOutput.analysis_run_id == analysis_run_id)
            .order_by(FxAgentOutput.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_consensus(self, analysis_run_id: str) -> FxConsensusRun | None:
        result = await self._session.execute(
            select(FxConsensusRun).where(
                FxConsensusRun.analysis_run_id == analysis_run_id
            )
        )
        return result.scalar_one_or_none()

    async def list_signals(self, tenant_id: str, *, limit: int = 50) -> list[FxSignalRow]:
        result = await self._session.execute(
            select(FxSignalRow)
            .where(FxSignalRow.tenant_id == tenant_id)
            .order_by(FxSignalRow.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_news(self, *, limit: int = 50) -> list[FxNewsItem]:
        result = await self._session.execute(
            select(FxNewsItem)
            .order_by(FxNewsItem.published_at.desc().nullslast(), FxNewsItem.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_macro(self, *, limit: int = 100) -> list[FxMacroEvent]:
        result = await self._session.execute(
            select(FxMacroEvent)
            .order_by(FxMacroEvent.scheduled_at.desc().nullslast(), FxMacroEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_pending_evaluations(
        self, *, limit: int = 50
    ) -> list[FxAnalysisEvaluation]:
        result = await self._session.execute(
            select(FxAnalysisEvaluation)
            .where(FxAnalysisEvaluation.evaluation_status == "pending")
            .order_by(FxAnalysisEvaluation.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def save_evaluation(self, **fields) -> FxAnalysisEvaluation:
        row = FxAnalysisEvaluation(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_evaluation(
        self, eval_id: uuid.UUID | str, **fields
    ) -> FxAnalysisEvaluation | None:
        parsed = eval_id if isinstance(eval_id, uuid.UUID) else uuid.UUID(str(eval_id))
        result = await self._session.execute(
            select(FxAnalysisEvaluation).where(FxAnalysisEvaluation.id == parsed)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row

    async def _get_evaluation_by_run_horizon(
        self, *, analysis_run_id: str, horizon: str
    ) -> FxAnalysisEvaluation | None:
        result = await self._session.execute(
            select(FxAnalysisEvaluation).where(
                FxAnalysisEvaluation.analysis_run_id == analysis_run_id,
                FxAnalysisEvaluation.horizon == horizon,
            )
        )
        return result.scalar_one_or_none()

    async def create_pending_evaluations_for_run(
        self,
        tenant_id: str,
        analysis_run_id: str,
        instrument: str,
        price_at_analysis: str | None,
    ) -> list[FxAnalysisEvaluation]:
        created: list[FxAnalysisEvaluation] = []
        for horizon in _EVALUATION_HORIZONS:
            existing = await self._get_evaluation_by_run_horizon(
                analysis_run_id=analysis_run_id,
                horizon=horizon,
            )
            if existing is not None:
                continue
            row = await self.save_evaluation(
                tenant_id=tenant_id,
                analysis_run_id=analysis_run_id,
                instrument=instrument,
                horizon=horizon,
                price_at_analysis=price_at_analysis,
                evaluation_status="pending",
            )
            created.append(row)
        return created


    async def save_paper_order(self, order: dict) -> FxPaperOrder:
        from datetime import datetime, timezone

        def _dt(v):
            if not v:
                return None
            if isinstance(v, datetime):
                return v
            return datetime.fromisoformat(str(v).replace("Z", "+00:00"))

        row = FxPaperOrder(
            tenant_id=order.get("tenant_id") or "default",
            order_key=order["order_id"],
            instrument=order["instrument"],
            side=order["side"],
            order_type=order["order_type"],
            quantity=float(order["quantity"]),
            limit_price=order.get("limit_price"),
            stop_loss=order.get("stop_loss"),
            take_profit=order.get("take_profit"),
            status=order["status"],
            fill_price=order.get("fill_price"),
            filled_at=_dt(order.get("filled_at")),
            signal_id=order.get("signal_id"),
            analysis_run_id=order.get("analysis_run_id"),
            payload=order,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def save_paper_position(self, position: dict) -> FxPaperPosition:
        from datetime import datetime

        def _dt(v):
            if not v:
                return None
            if isinstance(v, datetime):
                return v
            return datetime.fromisoformat(str(v).replace("Z", "+00:00"))

        row = FxPaperPosition(
            tenant_id=position.get("tenant_id") or "default",
            position_key=position["position_id"],
            order_key=position.get("order_id"),
            instrument=position["instrument"],
            side=position["side"],
            quantity=float(position["quantity"]),
            entry_price=float(position["entry_price"]),
            exit_price=position.get("exit_price"),
            stop_loss=position.get("stop_loss"),
            take_profit=position.get("take_profit"),
            status=position["status"],
            pnl=position.get("pnl"),
            opened_at=_dt(position.get("opened_at")),
            closed_at=_dt(position.get("closed_at")),
            signal_id=position.get("signal_id"),
            analysis_run_id=position.get("analysis_run_id"),
            payload=position,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def save_journal_entry(self, entry: dict) -> FxJournalEntry:
        row = FxJournalEntry(
            tenant_id=entry.get("tenant_id") or "default",
            journal_key=entry["journal_id"],
            instrument=entry.get("instrument"),
            entry_price=float(entry["entry"]) if entry.get("entry") is not None else None,
            exit_price=float(entry["exit"]) if entry.get("exit") is not None else None,
            pnl=entry.get("pnl"),
            duration_sec=entry.get("duration_sec"),
            signal_id=entry.get("signal_id"),
            analysis_run_id=entry.get("analysis_run_id"),
            payload=entry,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_paper_orders(self, tenant_id: str, *, limit: int = 200) -> list[FxPaperOrder]:
        from sqlalchemy import select

        q = (
            select(FxPaperOrder)
            .where(FxPaperOrder.tenant_id == (tenant_id or "default"))
            .order_by(FxPaperOrder.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(q)).scalars().all())

    async def list_paper_positions(self, tenant_id: str, *, limit: int = 200) -> list[FxPaperPosition]:
        from sqlalchemy import select

        q = (
            select(FxPaperPosition)
            .where(FxPaperPosition.tenant_id == (tenant_id or "default"))
            .order_by(FxPaperPosition.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(q)).scalars().all())

    async def list_journal_entries(self, tenant_id: str, *, limit: int = 200) -> list[FxJournalEntry]:
        from sqlalchemy import select

        q = (
            select(FxJournalEntry)
            .where(FxJournalEntry.tenant_id == (tenant_id or "default"))
            .order_by(FxJournalEntry.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(q)).scalars().all())

    async def upsert_paper_order(self, order: dict) -> FxPaperOrder:
        from datetime import datetime, timezone
        from sqlalchemy import select

        def _dt(v):
            if not v:
                return None
            if isinstance(v, datetime):
                return v
            return datetime.fromisoformat(str(v).replace("Z", "+00:00"))

        tenant = order.get("tenant_id") or "default"
        key = order["order_id"]
        q = select(FxPaperOrder).where(FxPaperOrder.tenant_id == tenant, FxPaperOrder.order_key == key)
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return await self.save_paper_order(order)
        row.instrument = order["instrument"]
        row.side = order["side"]
        row.order_type = order["order_type"]
        row.quantity = float(order["quantity"])
        row.limit_price = order.get("limit_price")
        row.stop_loss = order.get("stop_loss")
        row.take_profit = order.get("take_profit")
        row.status = order["status"]
        row.fill_price = order.get("fill_price")
        row.filled_at = _dt(order.get("filled_at"))
        row.signal_id = order.get("signal_id")
        row.analysis_run_id = order.get("analysis_run_id")
        row.payload = order
        await self._session.flush()
        return row

    async def upsert_paper_position(self, position: dict) -> FxPaperPosition:
        from datetime import datetime
        from sqlalchemy import select

        def _dt(v):
            if not v:
                return None
            if isinstance(v, datetime):
                return v
            return datetime.fromisoformat(str(v).replace("Z", "+00:00"))

        tenant = position.get("tenant_id") or "default"
        key = position["position_id"]
        q = select(FxPaperPosition).where(FxPaperPosition.tenant_id == tenant, FxPaperPosition.position_key == key)
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return await self.save_paper_position(position)
        row.order_key = position.get("order_id")
        row.instrument = position["instrument"]
        row.side = position["side"]
        row.quantity = float(position["quantity"])
        row.entry_price = float(position["entry_price"])
        row.exit_price = position.get("exit_price")
        row.stop_loss = position.get("stop_loss")
        row.take_profit = position.get("take_profit")
        row.status = position["status"]
        row.pnl = position.get("pnl")
        row.opened_at = _dt(position.get("opened_at"))
        row.closed_at = _dt(position.get("closed_at"))
        row.signal_id = position.get("signal_id")
        row.analysis_run_id = position.get("analysis_run_id")
        row.payload = position
        await self._session.flush()
        return row

    async def upsert_journal_entry(self, entry: dict) -> FxJournalEntry:
        from sqlalchemy import select

        tenant = entry.get("tenant_id") or "default"
        key = entry["journal_id"]
        q = select(FxJournalEntry).where(FxJournalEntry.tenant_id == tenant, FxJournalEntry.journal_key == key)
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return await self.save_journal_entry(entry)
        row.instrument = entry.get("instrument")
        row.entry_price = float(entry["entry"]) if entry.get("entry") is not None else None
        row.exit_price = float(entry["exit"]) if entry.get("exit") is not None else None
        row.pnl = entry.get("pnl")
        row.duration_sec = entry.get("duration_sec")
        row.signal_id = entry.get("signal_id")
        row.analysis_run_id = entry.get("analysis_run_id")
        row.payload = entry
        await self._session.flush()
        return row
