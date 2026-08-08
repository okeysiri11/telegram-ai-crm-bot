"""Observability — structured logs, health, heartbeat, diagnostics."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("hercules")


class HerculesTelemetry:
    def __init__(self) -> None:
        self.started_at = time.time()
        self.heartbeats = 0
        self.last_heartbeat: float | None = None
        self.crash_reports: list[dict[str, Any]] = []

    def log(self, event: str, **fields: Any) -> None:
        logger.info("hercules_event=%s %s", event, " ".join(f"{k}={v}" for k, v in fields.items()))

    def heartbeat(self) -> dict[str, Any]:
        self.heartbeats += 1
        self.last_heartbeat = time.time()
        return {"ok": True, "heartbeats": self.heartbeats, "ts": self.last_heartbeat}

    def health(self) -> dict[str, Any]:
        from platform_hercules.core.resources import resource_manager
        from platform_hercules.metrics.metrics import hercules_metrics

        return {
            "status": "ok",
            "uptime_sec": round(time.time() - self.started_at, 1),
            "resources": resource_manager.dashboard(),
            "metrics": hercules_metrics.dashboard(),
        }

    def report_crash(self, error: str, *, context: dict[str, Any] | None = None) -> None:
        self.crash_reports.append({"error": error, "context": context or {}, "ts": time.time()})
        logger.error("hercules_crash %s", error)

    def diagnostics(self) -> dict[str, Any]:
        return {
            "health": self.health(),
            "crashes": len(self.crash_reports),
            "otel": "structured_logs",  # hook point for OpenTelemetry exporters
        }


hercules_telemetry = HerculesTelemetry()
