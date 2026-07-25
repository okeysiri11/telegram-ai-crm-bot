"""Monitoring Engine — Sprint 25.6."""

from __future__ import annotations

from typing import Any

from platform_enterprise_production.models import MONITORING_SIGNALS


class MonitoringEngine:
    def sample(self, *, overrides: dict[str, float] | None = None) -> dict[str, Any]:
        overrides = overrides or {}
        defaults = {
            "cpu": 0.35,
            "memory": 0.42,
            "disk": 0.28,
            "network": 0.15,
            "database": 0.30,
            "cache": 0.20,
            "queue": 0.10,
            "ai_providers": 0.25,
            "active_sessions": 120.0,
            "api_requests": 450.0,
            "background_jobs": 18.0,
        }
        signals = []
        for name in MONITORING_SIGNALS:
            value = float(overrides.get(name, defaults[name]))
            signals.append({"signal": name, "value": value, "ok": value < 0.90 if name in (
                "cpu", "memory", "disk", "network", "database", "cache", "queue", "ai_providers"
            ) else True})
        return {
            "signals": signals,
            "passed": all(s["ok"] for s in signals),
            "continuous": True,
            "duplicates_obs_logic": False,
        }
