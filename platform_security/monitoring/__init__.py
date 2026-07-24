"""Security monitoring — Sprint 21.4."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from platform_security.models import MONITORING_SIGNALS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SecurityMonitoring:
    def __init__(self) -> None:
        self._alerts: list[dict[str, Any]] = []

    def detect(self, *, signal: str, severity: str = "medium", details: dict[str, Any] | None = None) -> dict[str, Any]:
        if signal not in MONITORING_SIGNALS:
            raise ValueError(f"unknown signal: {signal}")
        alert = {
            "alert_id": f"mon_{uuid.uuid4().hex[:12]}",
            "signal": signal,
            "severity": severity,
            "details": details or {},
            "detected_at": _now(),
        }
        self._alerts.append(alert)
        return alert

    def list_alerts(self) -> list[dict[str, Any]]:
        return list(self._alerts)

    def status(self) -> dict[str, Any]:
        return {"alerts": len(self._alerts), "signals": list(MONITORING_SIGNALS)}
