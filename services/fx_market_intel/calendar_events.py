"""Calendar event model + aggregation helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

CATEGORIES = {
    "MACRO",
    "NEWS",
    "ANALYSIS",
    "AGENT",
    "SIGNAL",
    "SESSION",
    "PAPER_TRADE",
    "MANUAL",
}

FILTER_KEYS = {
    "macro": "MACRO",
    "news": "NEWS",
    "analysis": "ANALYSIS",
    "agent": "AGENT",
    "signal": "SIGNAL",
    "session": "SESSION",
    "paper": "PAPER_TRADE",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_event(
    *,
    category: str,
    title: str,
    scheduled_at: str,
    instrument: str = "EUR/USD",
    source: str = "",
    status: str = "scheduled",
    importance: str = "medium",
    description: str = "",
    links: dict[str, Any] | None = None,
    tenant_id: str = "global",
    reminder: bool = False,
) -> dict[str, Any]:
    cat = category.upper() if category else "MANUAL"
    if cat not in CATEGORIES:
        cat = "MANUAL"
    return {
        "event_id": f"ce_{uuid.uuid4().hex[:12]}",
        "category": cat,
        "title": title,
        "scheduled_at": scheduled_at,
        "instrument": instrument,
        "source": source,
        "status": status,
        "importance": importance,
        "description": description,
        "reminder": reminder,
        "links": links or {},
        "tenant_id": tenant_id,
        "created_at": _now(),
    }


def filter_events(events: list[dict[str, Any]], enabled: dict[str, bool] | None) -> list[dict[str, Any]]:
    if not enabled:
        return events
    allow = {FILTER_KEYS[k] for k, v in enabled.items() if v and k in FILTER_KEYS}
    if enabled.get("manual", True):
        allow.add("MANUAL")
    return [e for e in events if e.get("category") in allow]
