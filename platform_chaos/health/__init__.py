"""Service Health Monitor — Sprint 25.3."""

from __future__ import annotations

from typing import Any


class ServiceHealthMonitor:
    def snapshot(self, *, services: list[str] | None = None, incidents: dict[str, int] | None = None) -> dict[str, Any]:
        services = list(services or ["enterprise_hub", "event_bus", "database", "ai_provider_hub"])
        incidents = dict(incidents or {})
        rows = []
        for svc in services:
            fail_count = int(incidents.get(svc, 0))
            rows.append({
                "service": svc,
                "status": "degraded" if fail_count else "healthy",
                "availability": round(max(0.5, 1.0 - fail_count * 0.05), 3),
                "recovery_time_ms": fail_count * 200,
                "failure_count": fail_count,
                "last_incident": "simulated" if fail_count else None,
                "current_state": "recovering" if fail_count else "stable",
            })
        return {"services": rows, "count": len(rows)}
