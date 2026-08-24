"""Durable persistence bridge — Postgres when available, memory fallback for tests."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from services.fx_market_intel import memory as mem

logger = logging.getLogger(__name__)


def _parse_dt(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


async def persist_full_analysis(result: dict[str, Any]) -> dict[str, Any]:
    """Persist analysis run + agents + consensus + signal + pending evaluations."""
    tenant_id = str(result.get("tenant_id") or "default")
    analysis = result.get("analysis") or {}
    consensus = result.get("consensus") or {}
    signal = result.get("signal")
    agent_votes = result.get("agent_outputs") or []
    snapshot = result.get("market_snapshot") or {}

    # Always keep in-process memory for unit tests / TG without DB
    mem_row = mem.record_analysis(
        tenant_id=tenant_id,
        instrument=str(analysis.get("instrument") or "EUR/USD"),
        agent=str(analysis.get("agent") or "Chief Market Analyst"),
        direction=str(analysis.get("direction") or consensus.get("overall_direction") or "NEUTRAL"),
        confidence=float(analysis.get("confidence") or consensus.get("overall_confidence") or 0),
        horizon=str(analysis.get("horizon") or "intraday"),
        payload=result.get("display") or result,
        price_at_analysis=analysis.get("price_at_analysis"),
        dxy_at_analysis=analysis.get("dxy_at_analysis"),
    )
    result.setdefault("analysis", {}).update({"analysis_id": mem_row["analysis_id"], **{k: mem_row[k] for k in ("created_at", "evaluation_status") if k in mem_row}})

    try:
        from database.session import get_session
        from repositories.fx_market_intel_repository import FxMarketIntelRepository

        async with get_session() as session:
            repo = FxMarketIntelRepository(session)
            snap = None
            if snapshot:
                snap = await repo.save_snapshot(
                    tenant_id=tenant_id,
                    symbol=str(snapshot.get("symbol") or "EUR/USD"),
                    timeframe=snapshot.get("timeframe"),
                    mid=snapshot.get("mid"),
                    bid=snapshot.get("bid"),
                    ask=snapshot.get("ask"),
                    source=snapshot.get("source"),
                    status=snapshot.get("status"),
                    fetched_at=_parse_dt(snapshot.get("fetched_at")),
                    payload=snapshot,
                )
            run = await repo.save_analysis_run(
                tenant_id=tenant_id,
                user_id=result.get("user_id"),
                preset_id=result.get("preset_id"),
                analysis_type=str(result.get("analysis_type") or "full"),
                instrument=str(analysis.get("instrument") or "EUR/USD"),
                direction=analysis.get("direction") or consensus.get("overall_direction"),
                confidence=float(analysis.get("confidence") or consensus.get("overall_confidence") or 0),
                price_at_analysis=analysis.get("price_at_analysis"),
                dxy_at_analysis=analysis.get("dxy_at_analysis"),
                market_regime=analysis.get("market_regime"),
                missing_sources=result.get("missing_sources") or [],
                snapshot_id=str(snap.id) if snap else None,
                payload=result.get("display") or result,
                status="completed",
            )
            run_id = str(run.id)
            for ag in agent_votes:
                await repo.save_agent_output(
                    tenant_id=tenant_id,
                    analysis_run_id=run_id,
                    agent_id=str(ag.get("agent_id") or ag.get("id") or ""),
                    agent_name=ag.get("agent_name") or ag.get("name"),
                    vote=ag.get("vote"),
                    confidence=ag.get("confidence"),
                    summary=ag.get("summary"),
                    payload=ag,
                )
            if consensus:
                await repo.save_consensus(
                    tenant_id=tenant_id,
                    analysis_run_id=run_id,
                    overall_direction=consensus.get("overall_direction"),
                    overall_confidence=consensus.get("overall_confidence"),
                    disagreement_score=consensus.get("disagreement_score"),
                    payload=consensus,
                )
            if signal:
                await repo.save_signal(
                    tenant_id=tenant_id,
                    analysis_run_id=run_id,
                    signal_key=str(signal.get("signal_id") or run_id),
                    instrument=str(signal.get("instrument") or "EUR/USD"),
                    timeframe=signal.get("timeframe"),
                    signal=str(signal.get("signal") or "NO_SIGNAL"),
                    confidence=signal.get("confidence"),
                    price_at_signal=signal.get("price_at_signal") or analysis.get("price_at_analysis"),
                    entry_zone=signal.get("entry_zone"),
                    invalidation=signal.get("invalidation"),
                    reasons=signal.get("reasons"),
                    status=str(signal.get("status") or signal.get("signal") or "NO_SIGNAL"),
                    expires_at=_parse_dt(signal.get("expires_at")),
                    analytics_only=True,
                    trade_execution=False,
                    payload=signal,
                )
            await repo.create_pending_evaluations_for_run(
                tenant_id=tenant_id,
                analysis_run_id=run_id,
                instrument=str(analysis.get("instrument") or "EUR/USD"),
                price_at_analysis=analysis.get("price_at_analysis"),
            )
            result["persistence"] = {"status": "postgres", "analysis_run_id": run_id}
            result["analysis"]["analysis_run_id"] = run_id
            if signal:
                signal["analysis_run_id"] = run_id
            return result
    except Exception as exc:
        logger.warning("FX intel persistence fallback to memory: %s", exc)
        result["persistence"] = {"status": "memory", "reason": str(exc), "analysis_id": mem_row["analysis_id"]}
        return result


async def persist_news_items(items: list[dict[str, Any]]) -> int:
    if not items:
        return 0
    try:
        from database.session import get_session
        from repositories.fx_market_intel_repository import FxMarketIntelRepository

        n = 0
        async with get_session() as session:
            repo = FxMarketIntelRepository(session)
            for it in items:
                await repo.upsert_news(
                    {
                        "tenant_id": "global",
                        "source": it.get("source"),
                        "title": it.get("title"),
                        "url": it.get("url"),
                        "published_at": _parse_dt(it.get("published_at")),
                        "fetched_at": _parse_dt(it.get("fetched_at")) or datetime.now(timezone.utc),
                        "region": it.get("region"),
                        "instruments": it.get("instruments"),
                        "topics": it.get("topics"),
                        "importance": str(it.get("importance")) if it.get("importance") is not None else None,
                        "sentiment": it.get("sentiment"),
                        "ai_assessment": it.get("ai_assessment") or it.get("sentiment"),
                        "summary": it.get("summary"),
                        "duplicate_group_id": it.get("duplicate_group_id"),
                        "payload": it,
                    }
                )
                n += 1
        return n
    except Exception as exc:
        logger.warning("news persist skipped: %s", exc)
        return 0


async def persist_macro_events(events: list[dict[str, Any]]) -> int:
    if not events:
        return 0
    try:
        from database.session import get_session
        from repositories.fx_market_intel_repository import FxMarketIntelRepository

        n = 0
        async with get_session() as session:
            repo = FxMarketIntelRepository(session)
            for ev in events:
                await repo.upsert_macro(
                    {
                        "tenant_id": "global",
                        "event": ev.get("event") or "unknown",
                        "country": ev.get("country"),
                        "region": ev.get("region"),
                        "scheduled_at": _parse_dt(ev.get("scheduled_at")),
                        "actual": str(ev["actual"]) if ev.get("actual") is not None else None,
                        "forecast": str(ev["forecast"]) if ev.get("forecast") is not None else None,
                        "previous": str(ev["previous"]) if ev.get("previous") is not None else None,
                        "importance": str(ev.get("importance")) if ev.get("importance") is not None else None,
                        "affected_instruments": ev.get("affected_instruments"),
                        "status": ev.get("status") or "scheduled",
                        "external_key": ev.get("external_key"),
                        "payload": ev,
                    }
                )
                n += 1
        return n
    except Exception as exc:
        logger.warning("macro persist skipped: %s", exc)
        return 0


async def list_history(tenant_id: str = "default", limit: int = 50) -> list[dict[str, Any]]:
    try:
        from database.session import get_session
        from repositories.fx_market_intel_repository import FxMarketIntelRepository

        async with get_session() as session:
            repo = FxMarketIntelRepository(session)
            rows = await repo.list_analysis_runs(tenant_id, limit=limit)
            out = []
            for r in rows:
                out.append(
                    {
                        "analysis_run_id": str(r.id),
                        "tenant_id": r.tenant_id,
                        "preset_id": r.preset_id,
                        "instrument": r.instrument,
                        "direction": r.direction,
                        "confidence": r.confidence,
                        "price_at_analysis": r.price_at_analysis,
                        "dxy_at_analysis": r.dxy_at_analysis,
                        "market_regime": r.market_regime,
                        "missing_sources": r.missing_sources,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                        "payload": r.payload,
                        "status": r.status,
                    }
                )
            if out:
                return out
    except Exception as exc:
        logger.warning("history fallback memory: %s", exc)
    return mem.list_analyses(tenant_id)[-limit:][::-1]


async def get_history_detail(run_id: str, tenant_id: str = "default") -> dict[str, Any] | None:
    try:
        from database.session import get_session
        from repositories.fx_market_intel_repository import FxMarketIntelRepository

        async with get_session() as session:
            repo = FxMarketIntelRepository(session)
            run = await repo.get_analysis_run(run_id)
            if not run or (run.tenant_id not in (tenant_id, "default") and tenant_id not in ("default", run.tenant_id)):
                # allow default/demo cross-read only for matching tenant
                if run and run.tenant_id != tenant_id and tenant_id != "default":
                    return None
            if not run:
                return None
            agents = await repo.list_agent_outputs(str(run.id))
            consensus = await repo.get_consensus(str(run.id))
            return {
                "run": {
                    "analysis_run_id": str(run.id),
                    "tenant_id": run.tenant_id,
                    "preset_id": run.preset_id,
                    "instrument": run.instrument,
                    "direction": run.direction,
                    "confidence": run.confidence,
                    "price_at_analysis": run.price_at_analysis,
                    "dxy_at_analysis": run.dxy_at_analysis,
                    "market_regime": run.market_regime,
                    "missing_sources": run.missing_sources,
                    "created_at": run.created_at.isoformat() if run.created_at else None,
                    "payload": run.payload,
                },
                "agents": [
                    {
                        "agent_id": a.agent_id,
                        "agent_name": a.agent_name,
                        "vote": a.vote,
                        "confidence": a.confidence,
                        "summary": a.summary,
                    }
                    for a in agents
                ],
                "consensus": None
                if not consensus
                else {
                    "overall_direction": consensus.overall_direction,
                    "overall_confidence": consensus.overall_confidence,
                    "disagreement_score": consensus.disagreement_score,
                    "payload": consensus.payload,
                },
            }
    except Exception as exc:
        logger.warning("history detail failed: %s", exc)
        return None
