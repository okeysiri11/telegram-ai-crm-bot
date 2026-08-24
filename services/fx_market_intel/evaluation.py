"""Analytical accuracy evaluation hooks — never fabricates future outcomes."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any


HORIZONS = {
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
}


def direction_label(direction: str | None) -> str:
    d = (direction or "").upper()
    if d in {"WATCH_BUY", "BUY", "BULLISH"}:
        return "bullish"
    if d in {"WATCH_SELL", "SELL", "BEARISH"}:
        return "bearish"
    if d in {"NEUTRAL", "WAIT", "NO_SIGNAL"}:
        return "neutral"
    return "unknown"


def compute_move_metrics(
    *,
    price_at: float,
    price_after: float,
    predicted_direction: str | None,
    path_highs: list[float] | None = None,
    path_lows: list[float] | None = None,
) -> dict[str, Any]:
    """Fill evaluation fields from real later prices. No profitability claim."""
    move = price_after - price_at
    move_pct = (move / price_at) if price_at else 0.0
    pred = direction_label(predicted_direction)
    if pred == "bullish":
        correct = move > 0
    elif pred == "bearish":
        correct = move < 0
    elif pred == "neutral":
        correct = abs(move_pct) < 0.0015
    else:
        correct = None
    highs = path_highs or [price_after]
    lows = path_lows or [price_after]
    mfe = max(highs) - price_at
    mae = price_at - min(lows)
    outcome = "up" if move > 0 else "down" if move < 0 else "flat"
    return {
        "actual_move": round(move, 6),
        "actual_move_pct": round(move_pct, 6),
        "direction_correct": correct,
        "signal_outcome": outcome,
        "mfe": round(mfe, 6),
        "mae": round(mae, 6),
        "evaluation_status": "evaluated",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


def due_horizons(created_at: datetime, now: datetime | None = None) -> list[str]:
    now = now or datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    due = []
    for key, delta in HORIZONS.items():
        if now >= created_at + delta:
            due.append(key)
    return due
