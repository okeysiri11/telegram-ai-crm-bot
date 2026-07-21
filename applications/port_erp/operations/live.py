# Live Port Operations — operational facade over tracking engines.

from __future__ import annotations

from typing import Any

from applications.port_erp.tracking.engine import LiveTrackingEngine, live_tracking_engine


class LivePortOperations:
    """Live port operations view — vessels, containers, fleet, gates context."""

    def __init__(self, tracking: LiveTrackingEngine | None = None) -> None:
        self._tracking = tracking or live_tracking_engine

    def dashboard(self) -> dict[str, Any]:
        metrics = self._tracking.metrics()
        fleet = self._tracking.fleet.snapshot()
        return {
            "tracking_engine": "1.0",
            "metrics": metrics,
            "fleet": {
                "vessels": len(fleet["vessels"]),
                "containers": len(fleet["containers"]),
                "trucks": len(fleet["trucks"]),
                "rail": len(fleet["rail"]),
            },
            "recent_timeline": [e.to_dict() for e in self._tracking.timeline.recent(limit=20)],
        }


live_port_operations = LivePortOperations()
