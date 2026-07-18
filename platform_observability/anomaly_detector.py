# Anomaly detector — spikes, degradation, failures.

from __future__ import annotations

import logging
from typing import Any

from platform_observability.alert_manager import alert_manager
from platform_observability.models import AlertSeverity
from platform_observability.observability_events import MetricThresholdExceededEvent

logger = logging.getLogger(__name__)

THRESHOLDS: dict[str, tuple[float, str]] = {
    "api.request.duration_ms": (2000, "Slow API requests detected"),
    "jobs.queue.size": (1000, "Job queue growth anomaly"),
    "jobs.dead_letter.count": (10, "Dead letter queue spike"),
    "realtime.connections.count": (0, "Realtime connection drop"),  # checked separately
    "integrations.failures.total": (50, "Integration failure spike"),
}


class AnomalyDetector:
    def __init__(self) -> None:
        self._baselines: dict[str, float] = {}
        self._anomalies: list[dict[str, Any]] = []

    def reset(self) -> None:
        self._baselines.clear()
        self._anomalies.clear()

    async def analyze(self, metrics_summary: dict[str, Any]) -> list[dict[str, Any]]:
        detected: list[dict[str, Any]] = []

        for name, stats in metrics_summary.items():
            if name not in THRESHOLDS:
                continue
            threshold, message = THRESHOLDS[name]
            last = stats.get("last", 0)
            if last > threshold:
                anomaly = {
                    "type": "threshold_exceeded",
                    "metric": name,
                    "value": last,
                    "threshold": threshold,
                    "message": message,
                }
                detected.append(anomaly)
                self._anomalies.append(anomaly)
                await self._handle_threshold(name, last, threshold, message)

        detected.extend(await self._detect_retry_spikes())
        detected.extend(await self._detect_worker_failures())
        detected.extend(await self._detect_sla_degradation())

        return detected

    async def _handle_threshold(
        self,
        name: str,
        value: float,
        threshold: float,
        message: str,
    ) -> None:
        from events.event_bus import publish

        severity = AlertSeverity.CRITICAL.value if value > threshold * 2 else AlertSeverity.WARNING.value
        await publish(
            MetricThresholdExceededEvent(
                metric_name=name,
                value=value,
                threshold=threshold,
                severity=severity,
            )
        )
        await alert_manager.raise_alert(
            name=f"metric_threshold:{name}",
            severity=severity,
            source="anomaly_detector",
            message=f"{message} (value={value}, threshold={threshold})",
        )

    async def _detect_retry_spikes(self) -> list[dict[str, Any]]:
        try:
            from platform_jobs.job_metrics import job_metrics

            snap = await job_metrics.snapshot()
            if snap.retry_rate_per_min > 10:
                await alert_manager.raise_alert(
                    name="retry_spike",
                    severity=AlertSeverity.WARNING.value,
                    source="jobs",
                    message=f"Job retry rate spike: {snap.retry_rate_per_min}/min",
                )
                return [{"type": "retry_spike", "rate": snap.retry_rate_per_min}]
        except Exception:
            pass
        return []

    async def _detect_worker_failures(self) -> list[dict[str, Any]]:
        try:
            from platform_jobs.worker_manager import worker_manager

            summary = worker_manager.health_summary()
            unhealthy = summary.get("total", 0) - summary.get("healthy", 0)
            if unhealthy > 0 and summary.get("total", 0) > 0:
                await alert_manager.raise_alert(
                    name="worker_unhealthy",
                    severity=AlertSeverity.WARNING.value,
                    source="jobs",
                    message=f"{unhealthy} unhealthy workers",
                )
                return [{"type": "worker_failure", "unhealthy": unhealthy}]
        except Exception:
            pass
        return []

    async def _detect_sla_degradation(self) -> list[dict[str, Any]]:
        return []

    def recent_anomalies(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return self._anomalies[-limit:]


anomaly_detector = AnomalyDetector()
