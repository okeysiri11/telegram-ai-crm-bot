# MetricsManager — platform metrics collection and aggregation.

from __future__ import annotations

import logging
from typing import Any

from platform_observability.metrics_service import MetricsService, metrics_service

logger = logging.getLogger(__name__)


class MetricsManager:
    def __init__(self, *, metrics: MetricsService | None = None) -> None:
        self._metrics = metrics or metrics_service

    def reset(self) -> None:
        self._metrics.reset()

    def record(self, name: str, value: float, **kwargs) -> None:
        self._metrics.record(name, value, **kwargs)

    async def collect_all(self) -> list:
        return await self._metrics.collect_platform_metrics()

    async def collect_platform_engines(self) -> dict[str, Any]:
        """Collect metrics from AI platform engines via integration bridges."""
        engine_metrics: dict[str, Any] = {}

        engine_metrics["workflow"] = await self._workflow_metrics()
        engine_metrics["agent"] = await self._agent_metrics()
        engine_metrics["tool"] = await self._tool_metrics()
        engine_metrics["reasoning"] = await self._safe_summary("platform_reasoning", "reasoning_metrics")
        engine_metrics["planning"] = await self._safe_summary("platform_planning", "planning_metrics")
        engine_metrics["decision"] = await self._safe_summary("platform_decision", "decision_metrics")
        engine_metrics["learning"] = await self._safe_summary("platform_learning", "learning_metrics")
        engine_metrics["collaboration"] = await self._safe_summary("platform_collaboration", "collaboration_metrics")
        engine_metrics["security"] = await self._safe_summary("platform_security", "security_manager")

        for category, data in engine_metrics.items():
            if isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, (int, float)):
                        self._metrics.record(f"platform.{category}.{key}", float(val))

        return engine_metrics

    async def _workflow_metrics(self) -> dict[str, Any]:
        try:
            from platform_workflow.metrics import workflow_metrics

            summary = workflow_metrics.summary()
            self._metrics.record("workflow.duration_ms", summary.get("avg_completion_time_ms", 0), unit="ms")
            self._metrics.record("workflow.success_rate", summary.get("success_rate", 0))
            self._metrics.record("workflow.error_rate", summary.get("failure_rate", 0))
            self._metrics.record("jobs.queue.size", summary.get("queue_peak", 0))
            return summary
        except Exception:
            return {}

    async def _agent_metrics(self) -> dict[str, Any]:
        try:
            from platform_orchestrator.metrics import orchestrator_metrics

            summary = orchestrator_metrics.summary()
            self._metrics.record("agent.latency_ms", summary.get("avg_execution_time_ms", 0), unit="ms")
            self._metrics.record("agent.failure_rate", 1.0 - summary.get("success_rate", 1.0))
            self._metrics.record("platform.active_sessions", float(summary.get("active_agents", 0)))
            return summary
        except Exception:
            return {}

    async def _tool_metrics(self) -> dict[str, Any]:
        try:
            from platform_tools.metrics import tool_metrics

            summary = tool_metrics.summary()
            self._metrics.record("tool.latency_ms", summary.get("avg_execution_time_ms", 0), unit="ms")
            self._metrics.record("tool.failure_rate", summary.get("error_rate", 0))
            return summary
        except Exception:
            return {}

    async def _safe_summary(self, module: str, attr: str) -> dict[str, Any]:
        try:
            import importlib

            mod = importlib.import_module(module)
            obj = getattr(mod, attr)
            if hasattr(obj, "metrics_summary"):
                return obj.metrics_summary()
            if hasattr(obj, "summary"):
                return obj.summary()
        except Exception:
            logger.debug("metrics unavailable for %s.%s", module, attr)
        return {}

    def summary(self) -> dict[str, Any]:
        return self._metrics.summary()

    def query(self, **kwargs):
        return self._metrics.query(**kwargs)

    async def export_batch(self) -> list[dict[str, Any]]:
        return await self._metrics.flush_export_buffer()


metrics_manager = MetricsManager()
