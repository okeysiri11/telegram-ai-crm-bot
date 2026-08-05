"""Service health checker — heartbeat, metrics, availability."""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING

from platform_service_builder.models import ServiceHealthSnapshot, ServiceState

if TYPE_CHECKING:
    from platform_service_builder.models import ServiceDefinition


class ServiceHealthChecker:
    HEARTBEAT_STALE_SEC = 90.0

    def __init__(self) -> None:
        self._history: dict[str, list[ServiceHealthSnapshot]] = {}

    def reset(self) -> None:
        self._history.clear()

    def heartbeat(self, definition: ServiceDefinition, *, response_time_ms: float | None = None) -> ServiceHealthSnapshot:
        now = time.time()
        definition.last_heartbeat_at = now
        if response_time_ms is not None:
            definition.response_time_ms = response_time_ms
        elif definition.state == ServiceState.RUNNING:
            # Simulated probe for virtual services
            definition.response_time_ms = round(random.uniform(2.0, 40.0), 2)
            definition.cpu_pct = round(min(95.0, max(0.5, definition.cpu_pct * 0.7 + random.uniform(1.0, 12.0))), 2)
            definition.ram_mb = round(max(16.0, definition.ram_mb * 0.85 + random.uniform(8.0, 48.0)), 2)

        snap = self.snapshot(definition)
        self._history.setdefault(definition.id, []).append(snap)
        self._history[definition.id] = self._history[definition.id][-100:]
        return snap

    def snapshot(self, definition: ServiceDefinition) -> ServiceHealthSnapshot:
        now = time.time()
        stale = False
        if definition.state == ServiceState.RUNNING:
            if definition.last_heartbeat_at is None:
                stale = True
            else:
                stale = (now - definition.last_heartbeat_at) > self.HEARTBEAT_STALE_SEC

        healthy = definition.state in {
            ServiceState.RUNNING,
            ServiceState.LOADED,
            ServiceState.PAUSED,
        } and not stale and definition.state != ServiceState.FAILED

        if definition.state == ServiceState.FAILED:
            healthy = False

        # rolling availability from history
        hist = self._history.get(definition.id, [])
        if hist:
            ok = sum(1 for h in hist if h.healthy)
            availability = round(100.0 * ok / len(hist), 2)
        else:
            availability = 100.0 if healthy else (0.0 if definition.state == ServiceState.FAILED else 50.0)
        definition.availability_pct = availability

        return ServiceHealthSnapshot(
            service_id=definition.id,
            healthy=healthy,
            heartbeat_at=definition.last_heartbeat_at,
            response_time_ms=definition.response_time_ms,
            memory_mb=definition.ram_mb,
            cpu_pct=definition.cpu_pct,
            errors=definition.error_count,
            restart_count=definition.restart_count,
            availability_pct=availability,
            status=definition.state.value,
            details={
                "stale_heartbeat": stale,
                "enabled": definition.enabled,
                "uptime_sec": definition.uptime_sec,
            },
        )

    def history(self, service_id: str, *, limit: int = 50) -> list[ServiceHealthSnapshot]:
        return list(self._history.get(service_id, []))[-limit:]


health_checker = ServiceHealthChecker()
