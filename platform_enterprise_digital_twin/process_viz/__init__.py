"""Process Visualization — Sprint 24.5."""

from __future__ import annotations

from typing import Any


class ProcessVisualization:
    def render(self, *, processes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        processes = list(processes or [])
        running = [p for p in processes if p.get("status") == "running"]
        queued = [p for p in processes if p.get("status") == "queued"]
        completed = [p for p in processes if p.get("status") == "completed"]
        errors = [p for p in processes if p.get("status") == "error"]
        awaiting = [p for p in processes if p.get("status") in ("awaiting_approval", "pending_owner")]
        return {
            "running": running,
            "queued": queued,
            "completed": completed,
            "errors": errors,
            "awaiting_approval": awaiting,
            "total": len(processes),
        }
