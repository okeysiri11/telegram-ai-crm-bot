# Retention manager — configurable retention for telemetry data.

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from platform_observability.models import RetentionPolicy


class RetentionManager:
    def __init__(self) -> None:
        self._policy = RetentionPolicy()

    def reset(self) -> None:
        self._policy = RetentionPolicy()

    def get_policy(self) -> RetentionPolicy:
        return self._policy

    def set_policy(
        self,
        *,
        metrics_days: int | None = None,
        logs_days: int | None = None,
        traces_days: int | None = None,
        alerts_days: int | None = None,
    ) -> RetentionPolicy:
        if metrics_days is not None:
            self._policy.metrics_days = max(metrics_days, 1)
        if logs_days is not None:
            self._policy.logs_days = max(logs_days, 1)
        if traces_days is not None:
            self._policy.traces_days = max(traces_days, 1)
        if alerts_days is not None:
            self._policy.alerts_days = max(alerts_days, 1)
        return self._policy

    def apply(self) -> dict[str, int]:
        """Purge expired telemetry — returns counts purged."""
        from platform_observability.alert_manager import alert_manager
        from platform_observability.logging_service import logging_service
        from platform_observability.metrics_service import metrics_service
        from platform_observability.tracing_service import tracing_service

        now = datetime.now(timezone.utc)
        purged = {"metrics": 0, "logs": 0, "traces": 0, "alerts": 0}

        metrics_cutoff = now - timedelta(days=self._policy.metrics_days)
        before = len(metrics_service._points)
        metrics_service._points = [
            p for p in metrics_service._points if p.timestamp >= metrics_cutoff
        ]
        purged["metrics"] = before - len(metrics_service._points)

        logs_cutoff = now - timedelta(days=self._policy.logs_days)
        before = len(logging_service._entries)
        logging_service._entries = [
            e for e in logging_service._entries if e.timestamp >= logs_cutoff
        ]
        purged["logs"] = before - len(logging_service._entries)

        traces_cutoff = now - timedelta(days=self._policy.traces_days)
        before = len(tracing_service._spans)
        tracing_service._spans = [
            s for s in tracing_service._spans if s.started_at >= traces_cutoff
        ]
        purged["traces"] = before - len(tracing_service._spans)

        alerts_cutoff = now - timedelta(days=self._policy.alerts_days)
        to_remove = [
            aid
            for aid, a in alert_manager._alerts.items()
            if a.state == "recovered" and a.resolved_at and a.resolved_at < alerts_cutoff
        ]
        for aid in to_remove:
            del alert_manager._alerts[aid]
        purged["alerts"] = len(to_remove)

        return purged


retention_manager = RetentionManager()
