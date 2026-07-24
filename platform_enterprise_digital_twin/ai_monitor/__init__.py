"""AI Activity Monitor — Sprint 24.5."""

from __future__ import annotations

from typing import Any


class AIActivityMonitor:
    def monitor(self, *, agents: list[dict[str, Any]] | None = None, tasks: list[dict[str, Any]] | None = None, recommendations: list[str] | None = None, pending: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        agents = list(agents or [])
        tasks = list(tasks or [])
        recommendations = list(recommendations or [])
        pending = list(pending or [])
        active = [a for a in agents if a.get("status") == "active"]
        return {
            "active_agents": active,
            "active_count": len(active),
            "running_tasks": tasks,
            "recommendations": recommendations,
            "pending_approvals": pending,
            "effectiveness": {
                "tasks": len(tasks),
                "recommendations": len(recommendations),
                "pending": len(pending),
            },
        }
