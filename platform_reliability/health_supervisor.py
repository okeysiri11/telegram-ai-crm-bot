# HealthSupervisor — continuous monitoring and automatic recovery.

from __future__ import annotations

import logging
import time
from typing import Any

from platform_reliability.config import DEFAULT_RELIABILITY_CONFIG, ReliabilityConfig
from platform_reliability.models import RecoveryContext, RecoveryResult

logger = logging.getLogger(__name__)


class HealthSupervisor:
    def __init__(self, *, config: ReliabilityConfig | None = None) -> None:
        self._config = config or DEFAULT_RELIABILITY_CONFIG
        self._component_status: dict[str, str] = {}
        self._isolated: set[str] = set()
        self._recovery_reports: list[dict[str, Any]] = []

    def reset(self) -> None:
        self._component_status.clear()
        self._isolated.clear()
        self._recovery_reports.clear()

    async def supervise(self) -> dict[str, Any]:
        components = await self._check_components()
        recoveries: list[RecoveryResult] = []

        for name, status in components.items():
            previous = self._component_status.get(name)
            if status == "unhealthy":
                if name not in self._isolated:
                    self._isolated.add(name)
                    recovery = await self._attempt_recovery(name)
                    recoveries.append(recovery)
            elif status == "healthy" and name in self._isolated:
                self._isolated.discard(name)

            if previous and previous != status:
                logger.info("health_change component=%s %s -> %s", name, previous, status)
            self._component_status[name] = status

        report = {
            "components": components,
            "isolated": list(self._isolated),
            "recoveries": [r.to_dict() for r in recoveries],
            "checked_at": time.time(),
        }
        self._recovery_reports.append(report)
        return report

    async def _check_components(self) -> dict[str, str]:
        components: dict[str, str] = {}
        try:
            from platform_observability.health_manager import health_manager

            health = await health_manager.check_platform()
            for name, data in health.get("components", {}).items():
                components[name] = data.get("status", "unknown")
            for name, data in health.get("platform_engines", {}).items():
                components[f"engine:{name}"] = data.get("status", "unknown")
        except Exception:
            logger.debug("observability health bridge unavailable")
        return components

    async def _attempt_recovery(self, component: str) -> RecoveryResult:
        from platform_reliability.recovery_manager import recovery_manager

        ctx = RecoveryContext(component=component, error=f"{component} unhealthy", error_type="unavailable")
        result = await recovery_manager.recover(ctx)
        result.message = f"Auto-recovery for {component}: {result.message}"
        return result

    def is_isolated(self, component: str) -> bool:
        return component in self._isolated

    def release(self, component: str) -> None:
        self._isolated.discard(component)

    def latest_report(self) -> dict[str, Any] | None:
        return self._recovery_reports[-1] if self._recovery_reports else None


health_supervisor = HealthSupervisor()
