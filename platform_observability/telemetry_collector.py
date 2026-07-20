# TelemetryCollector — unified telemetry ingestion and alert evaluation.

from __future__ import annotations

import logging
from typing import Any

from platform_observability.alert_manager import AlertManager, alert_manager
from platform_observability.config import DEFAULT_ALERT_THRESHOLDS, DEFAULT_OBSERVABILITY_CONFIG, ObservabilityConfig
from platform_observability.metrics_manager import MetricsManager, metrics_manager
from platform_observability.models import AlertThreshold, MonitoringContext

logger = logging.getLogger(__name__)


class TelemetryCollector:
    def __init__(
        self,
        *,
        metrics: MetricsManager | None = None,
        alerts: AlertManager | None = None,
        config: ObservabilityConfig | None = None,
    ) -> None:
        self._metrics = metrics or metrics_manager
        self._alerts = alerts or alert_manager
        self._config = config or DEFAULT_OBSERVABILITY_CONFIG
        self._thresholds: list[AlertThreshold] = list(DEFAULT_ALERT_THRESHOLDS)
        self._context: MonitoringContext | None = None

    def reset(self) -> None:
        self._thresholds = list(DEFAULT_ALERT_THRESHOLDS)

    def set_context(self, ctx: MonitoringContext) -> None:
        self._context = ctx

    def configure_threshold(self, threshold: AlertThreshold) -> None:
        self._thresholds = [t for t in self._thresholds if t.name != threshold.name]
        self._thresholds.append(threshold)

    async def collect_cycle(self) -> dict[str, Any]:
        platform_points = await self._metrics.collect_all()
        engine_metrics = await self._metrics.collect_platform_engines()
        alerts_raised = await self.evaluate_alerts()
        return {
            "metrics_collected": len(platform_points),
            "engine_metrics": engine_metrics,
            "alerts_raised": len(alerts_raised),
        }

    async def evaluate_alerts(self) -> list[str]:
        summary = self._metrics.summary()
        raised: list[str] = []

        metric_values: dict[str, float] = {}
        for name, stats in summary.items():
            if isinstance(stats, dict) and "last" in stats:
                metric_values[name] = float(stats["last"])
            metric_values.setdefault(name.replace("platform.", ""), metric_values.get(name, 0))

        for threshold in self._thresholds:
            current = metric_values.get(threshold.metric, 0.0)
            if not threshold.metric.startswith("platform."):
                current = metric_values.get(threshold.metric.split(".")[-1], current)
            for name, stats in summary.items():
                if threshold.metric in name or name.endswith(threshold.metric.split(".")[-1]):
                    current = float(stats.get("last", current) if isinstance(stats, dict) else current)
                    break

            if threshold.evaluate(current):
                alert = await self._alerts.raise_alert(
                    name=threshold.name,
                    severity=threshold.severity,
                    source="telemetry_collector",
                    message=f"{threshold.metric}={current} threshold={threshold.value}",
                )
                if alert:
                    raised.append(alert.alert_id)

        return raised

    async def record_event_throughput(self, count: float) -> None:
        self._metrics.record("eventbus.events_per_second", count)


telemetry_collector = TelemetryCollector()
