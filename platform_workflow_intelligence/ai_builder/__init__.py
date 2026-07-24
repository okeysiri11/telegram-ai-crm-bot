"""AI Workflow Builder — Sprint 24.1."""

from __future__ import annotations

from typing import Any


class AIWorkflowBuilder:
    def analyze(self, workflow: dict[str, Any]) -> dict[str, Any]:
        nodes = list(workflow.get("nodes") or [])
        steps = len(nodes)
        bottlenecks = [n["node_id"] for n in nodes if n.get("type") in ("delay", "human_approval") and steps > 4]
        suggestions = []
        if steps > 6:
            suggestions.append("reduce_steps")
        if bottlenecks:
            suggestions.append("parallelize_or_preapprove")
        forecast_ms = steps * 800
        return {
            "workflow_id": workflow.get("workflow_id"),
            "steps": steps,
            "bottlenecks": bottlenecks,
            "optimization_suggestions": suggestions,
            "forecast_duration_ms": forecast_ms,
            "ai_may_act": False,
            "mutates_workflow": False,
            "proposes_only": True,
        }
