"""Macro / economic event model + adapter shell."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

MACRO_EVENT_TYPES = {
    "fed_rate",
    "ecb_rate",
    "cpi",
    "pce",
    "nfp",
    "gdp",
    "pmi",
    "employment",
    "unemployment",
    "cb_speech",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_macro_event(raw: dict[str, Any]) -> dict[str, Any]:
    et = str(raw.get("event") or raw.get("event_type") or "").strip().lower().replace(" ", "_")
    return {
        "id": str(raw.get("id") or f"macro_{uuid.uuid4().hex[:12]}"),
        "event": et or "unknown",
        "country": str(raw.get("country") or raw.get("region") or ""),
        "region": str(raw.get("region") or raw.get("country") or ""),
        "scheduled_at": raw.get("scheduled_at"),
        "actual": raw.get("actual"),
        "forecast": raw.get("forecast"),
        "previous": raw.get("previous"),
        "importance": raw.get("importance"),
        "affected_instruments": list(raw.get("affected_instruments") or ["EUR/USD", "DXY"]),
        "status": str(raw.get("status") or "scheduled"),
        "fetched_at": _now(),
    }


def empty_calendar_state() -> dict[str, Any]:
    return {
        "status": "not_connected",
        "message": "Экономический календарь не подключён",
        "events": [],
        "supported_types": sorted(MACRO_EVENT_TYPES),
    }
