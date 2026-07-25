"""Alert Manager — Sprint 25.6."""

from __future__ import annotations

from typing import Any

from platform_enterprise_production.models import ALERT_TRIGGERS


class AlertManager:
    def evaluate(self, *, active: list[str] | None = None) -> dict[str, Any]:
        active = list(active or [])
        unknown = [a for a in active if a not in ALERT_TRIGGERS]
        if unknown:
            raise ValueError(f"unknown alert triggers: {unknown}")
        alerts = [{"trigger": t, "active": t in active, "severity": "critical" if t in (
            "service_failure", "database_failure", "critical_security_event"
        ) else "warning"} for t in ALERT_TRIGGERS]
        critical = [a for a in alerts if a["active"] and a["severity"] == "critical"]
        return {
            "alerts": alerts,
            "active_count": sum(1 for a in alerts if a["active"]),
            "critical_count": len(critical),
            "intelligent": True,
            "blocks_release": len(critical) > 0,
        }
