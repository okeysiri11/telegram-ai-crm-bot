"""Provider health monitor — independent from Recruiting infrastructure health."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.recruiting_ops.provider_connections import PROVIDERS, public_card

_MONITOR: dict[str, dict[str, Any]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_check(provider: str, result: dict[str, Any]) -> dict[str, Any]:
    key = (provider or "").strip().lower()
    prev = _MONITOR.get(key) or {"consecutive_failures": 0}
    ok = bool(result.get("ok") and result.get("connected"))
    failures = 0 if ok else int(prev.get("consecutive_failures") or 0) + 1
    status = "CONNECTED" if ok else (result.get("status") or "ERROR")
    if failures >= 3 and status == "ERROR":
        status = "DEGRADED" if result.get("error") in {"RATE_LIMITED", "PROVIDER_UNAVAILABLE"} else "ERROR"
    row = {
        "provider": key,
        "mode": result.get("mode") or "LIVE",
        "status": status,
        "last_check": _now(),
        "last_success": _now() if ok else prev.get("last_success"),
        "latency": result.get("latency_ms"),
        "consecutive_failures": failures,
        "last_error_code": None if ok else (result.get("error_code") or result.get("error")),
        "connected": ok,
        "mock": bool(result.get("mock") or result.get("mode") == "MOCK"),
        "infra_independent": True,
    }
    _MONITOR[key] = row
    return row


def monitor_snapshot(connections: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    items = []
    by = {(item.get("provider") or ""): item for item in connections or []}
    for provider in PROVIDERS:
        recorded = _MONITOR.get(provider)
        card = public_card(by.get(provider) or {"provider": provider, "status": "NOT_CONFIGURED", "mode": "LIVE"})
        items.append(
            recorded
            or {
                "provider": provider,
                "mode": card["mode"],
                "status": card["status"],
                "last_check": card.get("last_successful_health_check"),
                "last_success": card.get("last_successful_health_check"),
                "latency": card.get("latency_ms"),
                "consecutive_failures": 0,
                "last_error_code": card.get("last_error"),
                "connected": card["connected"],
                "mock": card["mock"],
                "infra_independent": True,
            }
        )
    return {
        "ok": True,
        "items": items,
        "infra_independent": True,
        "core_down": False,
        "message_ru": "Сбой провайдера не означает, что инфраструктура Recruiting недоступна.",
    }


def reset_health_monitor() -> None:
    _MONITOR.clear()
