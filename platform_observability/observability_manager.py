# ObservabilityManager — unified observability layer entry point.

from __future__ import annotations

import logging
from typing import Any

from platform_observability.alert_manager import AlertManager, alert_manager
from platform_observability.config import ObservabilityConfig, DEFAULT_OBSERVABILITY_CONFIG
from platform_observability.diagnostic_manager import DiagnosticManager, diagnostic_manager
from platform_observability.health_manager import HealthManager, health_manager
from platform_observability.integrations import ObservabilityIntegrations, observability_integrations
from platform_observability.log_manager import LogManager, log_manager
from platform_observability.metrics_manager import MetricsManager, metrics_manager
from platform_observability.models import AlertThreshold, MonitoringContext
from platform_observability.telemetry_collector import TelemetryCollector, telemetry_collector
from platform_observability.trace_manager import TraceManager, trace_manager

logger = logging.getLogger(__name__)


class ObservabilityManager:
    """Central observability facade — logging, tracing, metrics, health, alerts, diagnostics."""

    def __init__(
        self,
        *,
        logs: LogManager | None = None,
        traces: TraceManager | None = None,
        metrics: MetricsManager | None = None,
        health: HealthManager | None = None,
        alerts: AlertManager | None = None,
        diagnostics: DiagnosticManager | None = None,
        telemetry: TelemetryCollector | None = None,
        integrations: ObservabilityIntegrations | None = None,
        config: ObservabilityConfig | None = None,
    ) -> None:
        self._logs = logs or log_manager
        self._traces = traces or trace_manager
        self._metrics = metrics or metrics_manager
        self._health = health or health_manager
        self._alerts = alerts or alert_manager
        self._diagnostics = diagnostics or diagnostic_manager
        self._telemetry = telemetry or telemetry_collector
        self._integrations = integrations or observability_integrations
        self._config = config or DEFAULT_OBSERVABILITY_CONFIG

    def reset(self) -> None:
        self._traces.reset()
        self._metrics.reset()
        self._health.reset()
        self._alerts.reset()
        self._diagnostics.reset()
        self._telemetry.reset()

    def create_context(self, **kwargs) -> MonitoringContext:
        return self._integrations.context_from_request(**kwargs)

    def bind_context(self, ctx: MonitoringContext) -> None:
        self._logs.apply_context(ctx)
        self._telemetry.set_context(ctx)

    async def collect_telemetry(self) -> dict[str, Any]:
        return await self._telemetry.collect_cycle()

    async def check_health(self) -> dict[str, Any]:
        return await self._health.check_platform()

    async def diagnose(self, **kwargs):
        return await self._diagnostics.generate_report(**kwargs)

    def configure_alert(self, threshold: AlertThreshold) -> None:
        self._telemetry.configure_threshold(threshold)

    async def raise_alert(self, **kwargs):
        return await self._alerts.raise_alert(**kwargs)

    def metrics_summary(self) -> dict[str, Any]:
        return self._metrics.summary()

    def export_traces(self, **kwargs) -> list[dict[str, Any]]:
        return self._traces.export_traces(**kwargs)

    def query_logs(self, **kwargs) -> list[dict[str, Any]]:
        return self._logs.query(**kwargs)


observability_manager = ObservabilityManager()
