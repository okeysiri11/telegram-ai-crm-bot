"""Autoscaling policies — Sprint 21.7."""

from __future__ import annotations

from typing import Any


class Autoscaling:
    def policies(self) -> dict[str, Any]:
        return {
            "policies": [
                {"service": "api", "metric": "cpu", "target": 65},
                {"service": "event_bus", "metric": "queue_depth", "target": 100},
                {"service": "ai", "metric": "latency_p95", "target": 700},
            ],
            "enabled": True,
        }
