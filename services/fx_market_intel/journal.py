"""Paper trade journal — evaluation dataset, no model training."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def journal_from_closed_position(
    position: dict[str, Any],
    *,
    consensus: dict[str, Any] | None = None,
    market_context: dict[str, Any] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    result = position.get("result")
    if result is None and position.get("pnl") is not None:
        pnl = float(position["pnl"])
        result = "win" if pnl > 0 else "loss" if pnl < 0 else "flat"
    return {
        "journal_id": f"jn_{uuid.uuid4().hex[:12]}",
        "tenant_id": position.get("tenant_id") or "default",
        "position_id": position.get("position_id"),
        "order_id": position.get("order_id"),
        "instrument": position.get("instrument"),
        "side": position.get("side"),
        "entry": position.get("entry_price"),
        "exit": position.get("exit_price"),
        "stop_loss": position.get("stop_loss"),
        "take_profit": position.get("take_profit"),
        "pnl": position.get("pnl"),
        "pnl_pips": position.get("pnl_pips"),
        "duration_sec": position.get("duration_sec"),
        "result": result,
        "event": "PAPER_POSITION_CLOSED",
        "kind": "PAPER_POSITION_CLOSED",
        "signal_id": position.get("signal_id"),
        "analysis_run_id": position.get("analysis_run_id"),
        "agent_result_id": position.get("agent_result_id"),
        "agent_consensus": consensus,
        "notes": notes or position.get("notes") or "",
        "market_context": market_context or {},
        "close_reason": position.get("close_reason"),
        "source": "paper",
        "why_opened": position.get("notes") or "Бумажная сделка по сигналу/анализу",
        "created_at": _now(),
        "date": (position.get("closed_at") or _now())[:10],
        "paper": True,
        "purpose": "agent_quality_evaluation",
        "training_enabled": False,
        "links": {
            "paper": f"?view=paper&position_id={position.get('position_id')}",
            "journal": "?view=journal",
        },
    }


def journal_position_opened(
    position: dict[str, Any],
    order: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Lifecycle event when a paper position opens (MARKET fill or LIMIT fill)."""
    order = order or {}
    risk = order.get("risk") if isinstance(order.get("risk"), dict) else position.get("risk") or {}
    return {
        "journal_id": f"jn_{uuid.uuid4().hex[:12]}",
        "tenant_id": position.get("tenant_id") or "default",
        "position_id": position.get("position_id"),
        "order_id": position.get("order_id") or order.get("order_id"),
        "instrument": position.get("instrument"),
        "side": position.get("side"),
        "entry": position.get("entry_price"),
        "exit": None,
        "stop_loss": position.get("stop_loss"),
        "take_profit": position.get("take_profit"),
        "pnl": None,
        "pnl_pips": None,
        "duration_sec": None,
        "result": "open",
        "event": "PAPER_POSITION_OPENED",
        "kind": "PAPER_POSITION_OPENED",
        "signal_id": position.get("signal_id") or order.get("signal_id"),
        "analysis_run_id": position.get("analysis_run_id") or order.get("analysis_run_id"),
        "agent_result_id": position.get("agent_result_id") or order.get("agent_result_id"),
        "agent_consensus": None,
        "notes": order.get("notes") or position.get("notes") or "",
        "market_context": {"source": "paper_open"},
        "close_reason": None,
        "source": "paper",
        "why_opened": order.get("notes") or "Бумажная сделка открыта",
        "created_at": _now(),
        "date": (position.get("opened_at") or _now())[:10],
        "paper": True,
        "purpose": "agent_quality_evaluation",
        "training_enabled": False,
        "risk": risk,
        "links": {
            "paper": f"?view=paper&position_id={position.get('position_id')}",
            "journal": "?view=journal",
        },
    }
