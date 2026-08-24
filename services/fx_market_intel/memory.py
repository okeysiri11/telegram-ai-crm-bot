"""Analysis memory records — outcomes left unevaluated (no fabricated futures)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

_STORE: dict[str, list[dict[str, Any]]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_analysis(
    *,
    tenant_id: str,
    instrument: str,
    agent: str,
    direction: str,
    confidence: float,
    horizon: str,
    payload: dict[str, Any],
    price_at_analysis: str | None = None,
    dxy_at_analysis: str | None = None,
) -> dict[str, Any]:
    aid = f"an_{uuid.uuid4().hex[:12]}"
    row = {
        "analysis_id": aid,
        "instrument": instrument,
        "created_at": _now(),
        "price_at_analysis": price_at_analysis,
        "DXY_at_analysis": dxy_at_analysis,
        "agent": agent,
        "direction": direction,
        "confidence": confidence,
        "horizon": horizon,
        "payload": payload,
        "result_after_1h": None,
        "result_after_4h": None,
        "result_after_1d": None,
        "evaluation_status": "pending",
        "tenant_id": tenant_id or "default",
    }
    key = row["tenant_id"]
    _STORE.setdefault(key, []).append(row)
    return row


def list_analyses(tenant_id: str = "default") -> list[dict[str, Any]]:
    return list(_STORE.get(tenant_id or "default", []))


def performance_metrics(tenant_id: str = "default") -> dict[str, Any]:
    rows = [r for r in list_analyses(tenant_id) if r.get("evaluation_status") == "evaluated"]
    if len(rows) < 5:
        return {
            "status": "insufficient_observations",
            "message": "Метрики появятся после достаточного числа оценённых наблюдений",
            "count_evaluated": len(rows),
            "agent_accuracy": None,
            "signal_accuracy": None,
            "average_confidence": None,
            "accuracy_by_horizon": {},
            "accuracy_by_market_regime": {},
        }
    confs = [float(r.get("confidence") or 0) for r in rows]
    return {
        "status": "ok",
        "count_evaluated": len(rows),
        "agent_accuracy": None,  # filled by evaluation jobs later
        "signal_accuracy": None,
        "average_confidence": round(sum(confs) / len(confs), 3) if confs else None,
        "accuracy_by_horizon": {},
        "accuracy_by_market_regime": {},
        "message": "Оценочные хуки готовы; исходы заполняются job-ами по историческим данным",
    }


def reset_memory_for_tests() -> None:
    _STORE.clear()
