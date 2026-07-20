# DiagnosticManager — timelines, performance reports, failure analysis.

from __future__ import annotations

import logging
from typing import Any

from platform_observability.log_manager import LogManager, log_manager
from platform_observability.metrics_manager import MetricsManager, metrics_manager
from platform_observability.models import DiagnosticReport
from platform_observability.trace_manager import TraceManager, trace_manager

logger = logging.getLogger(__name__)


class DiagnosticManager:
    def __init__(
        self,
        *,
        logs: LogManager | None = None,
        traces: TraceManager | None = None,
        metrics: MetricsManager | None = None,
    ) -> None:
        self._logs = logs or log_manager
        self._traces = traces or trace_manager
        self._metrics = metrics or metrics_manager
        self._history: list[DiagnosticReport] = []

    def reset(self) -> None:
        self._history.clear()

    async def generate_report(
        self,
        title: str = "Platform Diagnostic Report",
        *,
        correlation_id: str | None = None,
        workflow_id: str | None = None,
    ) -> DiagnosticReport:
        timeline = self._build_timeline(correlation_id=correlation_id, workflow_id=workflow_id)
        performance = self._performance_summary()
        failures = self._failure_analysis(correlation_id=correlation_id)
        dependencies = await self._dependency_analysis()
        historical = self._historical_metrics()

        report = DiagnosticReport(
            title=title,
            timeline=timeline,
            performance=performance,
            failures=failures,
            dependencies=dependencies,
            historical=historical,
        )
        self._history.append(report)
        return report

    def _build_timeline(
        self,
        *,
        correlation_id: str | None,
        workflow_id: str | None,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        logs = self._logs.query(correlation_id=correlation_id, workflow_id=workflow_id, limit=50)
        for entry in logs:
            events.append({"type": "log", "timestamp": entry.get("timestamp"), "message": entry.get("message")})
        for span in self._traces.slowest(limit=10):
            events.append({"type": "trace", "name": span.get("name"), "duration_ms": span.get("duration_ms")})
        events.sort(key=lambda e: str(e.get("timestamp", "")))
        return events

    def _performance_summary(self) -> dict[str, Any]:
        from platform_observability.performance_monitor import performance_monitor

        return {
            "metrics": self._metrics.summary(),
            "api": performance_monitor.summary(),
            "slow_traces": self._traces.slowest(limit=5),
        }

    def _failure_analysis(self, *, correlation_id: str | None) -> list[dict[str, Any]]:
        errors = self._logs.query(level="ERROR", correlation_id=correlation_id, limit=20)
        return [{"message": e.get("message"), "component": e.get("component"), "agent_id": e.get("agent_id")} for e in errors]

    async def _dependency_analysis(self) -> dict[str, Any]:
        from platform_observability.health_manager import health_manager

        return await health_manager.check_dependencies()

    def _historical_metrics(self) -> dict[str, Any]:
        return {"reports_generated": len(self._history), "metrics_summary": self._metrics.summary()}

    def list_reports(self) -> list[DiagnosticReport]:
        return list(self._history)


diagnostic_manager = DiagnosticManager()
