# HealthManager — platform, agent, workflow, tool, memory, dependency health.

from __future__ import annotations

import logging
from typing import Any

from platform_observability.health_monitor import HealthMonitor, health_monitor

logger = logging.getLogger(__name__)


class HealthManager:
    def __init__(self, *, monitor: HealthMonitor | None = None) -> None:
        self._monitor = monitor or health_monitor

    def reset(self) -> None:
        self._monitor.reset()

    async def check_platform(self) -> dict[str, Any]:
        report = await self._monitor.check_all()
        report["platform_engines"] = {
            "workflow": await self.check_workflow(),
            "agents": await self.check_agents(),
            "tools": await self.check_tools(),
            "memory": await self.check_memory(),
        }
        return report

    async def check_workflow(self) -> dict[str, Any]:
        try:
            from platform_workflow.metrics import workflow_metrics

            summary = workflow_metrics.summary()
            rate = summary.get("success_rate", 1.0)
            status = "healthy" if rate >= 0.8 else ("degraded" if rate >= 0.5 else "unhealthy")
            return {"status": status, "success_rate": rate, "executions": summary.get("executions", 0)}
        except Exception as exc:
            return {"status": "unknown", "error": str(exc)}

    async def check_agents(self) -> dict[str, Any]:
        try:
            from platform_agents.registry import agent_registry

            stats = agent_registry.summary()
            enabled = stats.get("enabled", 0)
            total = stats.get("total", 0)
            status = "healthy" if enabled > 0 or total == 0 else "degraded"
            return {"status": status, "enabled": enabled, "total": total}
        except Exception as exc:
            return {"status": "unknown", "error": str(exc)}

    async def check_tools(self) -> dict[str, Any]:
        try:
            from platform_tools.metrics import tool_metrics

            summary = tool_metrics.summary()
            error_rate = summary.get("error_rate", 0)
            status = "healthy" if error_rate < 0.2 else ("degraded" if error_rate < 0.5 else "unhealthy")
            return {"status": status, "error_rate": error_rate, "executions": summary.get("executions", 0)}
        except Exception as exc:
            return {"status": "unknown", "error": str(exc)}

    async def check_memory(self) -> dict[str, Any]:
        try:
            from platform_memory.context_assembler import ContextAssembler

            assembler = ContextAssembler()
            _ = assembler  # bridge available
            return {"status": "healthy", "engine": "platform_memory"}
        except Exception as exc:
            return {"status": "degraded", "error": str(exc)}

    async def check_dependencies(self) -> dict[str, Any]:
        base = await self._monitor.check_all()
        return base.get("components", {})


health_manager = HealthManager()
