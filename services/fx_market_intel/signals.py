"""Analytical signal engine — NEVER executes trades."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

SIGNAL_STATUSES = {
    "BUY_BIAS",
    "SELL_BIAS",
    "WATCH_BUY",
    "WATCH_SELL",
    "NEUTRAL",
    "WAIT",
    "HIGH_RISK",
    "NO_SIGNAL",
}

# Invariant: this module must not import broker/order execution.


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_signal(
    *,
    instrument: str,
    timeframe: str,
    signal: str,
    confidence: float,
    reasons: list[str] | None = None,
    support: float | None = None,
    resistance: float | None = None,
    entry_zone: str | None = None,
    invalidation: str | None = None,
    agent_votes: list[dict[str, Any]] | None = None,
    risk_events: list[str] | None = None,
    tenant_id: str = "",
    analysis_run_id: str | None = None,
    price_at_signal: str | float | None = None,
    price_trigger: dict[str, Any] | None = None,
    source: str = "analysis",
) -> dict[str, Any]:
    status = signal if signal in SIGNAL_STATUSES else "NO_SIGNAL"
    conf = max(0.0, min(1.0, float(confidence)))
    ts = _now()
    trigger = None
    if price_trigger:
        trigger = {
            "enabled": bool(price_trigger.get("enabled", True)),
            "price": float(price_trigger["price"]) if price_trigger.get("price") is not None else None,
            "direction": str(price_trigger.get("direction") or "cross"),
            "triggered": False,
            "triggered_at": None,
        }
    return {
        "signal_id": f"sig_{uuid.uuid4().hex[:12]}",
        "instrument": instrument,
        "timestamp": ts.isoformat(),
        "timeframe": timeframe,
        "signal": status,
        "confidence": round(conf, 3),
        "entry_zone": entry_zone,
        "support": support,
        "resistance": resistance,
        "invalidation": invalidation,
        "reasons": reasons or [],
        "agent_votes": agent_votes or [],
        "risk_events": risk_events or [],
        "expires_at": (ts + timedelta(hours=4)).isoformat(),
        "status": status,
        "status_ru": {
            "BUY_BIAS": "Склонность к покупке",
            "SELL_BIAS": "Склонность к продаже",
            "WATCH_BUY": "Наблюдать покупку",
            "WATCH_SELL": "Наблюдать продажу",
            "WAIT": "Ждать",
            "HIGH_RISK": "Высокий риск",
            "NO_SIGNAL": "Нет сигнала",
            "NEUTRAL": "Нейтрально",
        }.get(status, status),
        "tenant_id": tenant_id,
        "analysis_run_id": analysis_run_id,
        "price_at_signal": str(price_at_signal) if price_at_signal is not None else None,
        "price_trigger": trigger,
        "source": source,
        "links": {
            "analysis": f"?view=intel_history&run_id={analysis_run_id}" if analysis_run_id else None,
            "paper": "?view=paper",
            "chart": f"?view=charts&symbol={instrument}",
        },
        "analytics_only": True,
        "trade_execution": False,
        "disclaimer": "AI-анализ, не является гарантией результата.",
    }


def assert_no_trade_execution(payload: dict[str, Any]) -> None:
    if payload.get("trade_execution") is True:
        raise RuntimeError("Signal engine must not enable trade execution")
    if payload.get("analytics_only") is not True:
        raise RuntimeError("Signal must be analytics_only")


def evaluate_price_trigger(signal: dict[str, Any], mark_price: float) -> dict[str, Any]:
    """Mark trigger fired; does NOT execute trades."""
    trig = signal.get("price_trigger")
    if not trig or not trig.get("enabled") or trig.get("triggered") or trig.get("price") is None:
        return signal
    target = float(trig["price"])
    direction = str(trig.get("direction") or "cross")
    hit = False
    if direction == "above":
        hit = mark_price >= target
    elif direction == "below":
        hit = mark_price <= target
    else:
        hit = abs(mark_price - target) <= max(0.0001, target * 0.0002)
    if not hit:
        return signal
    out = {**signal, "price_trigger": {**trig, "triggered": True, "triggered_at": _now().isoformat()}}
    assert_no_trade_execution(out)
    return out
