"""AI Optimization after runs — Sprint 24.1."""

from __future__ import annotations

from typing import Any


class AIOptimization:
    def improve(self, *, analytics: dict[str, Any]) -> dict[str, Any]:
        tips = []
        if float(analytics.get("avg_duration_ms", 0)) > 5000:
            tips.append("reduce_latency")
        if analytics.get("errors"):
            tips.append("add_retries_or_compensation")
        if float(analytics.get("process_cost", 0)) > 100:
            tips.append("cut_expensive_steps")
        if not analytics.get("success_rate_95pct", True):
            tips.append("stabilize_failing_branches")
        if not tips:
            tips.append("maintain_current_design")
        return {
            "suggestions": tips,
            "analyzed": ["speed", "errors", "cost", "efficiency"],
            "ai_may_act": False,
            "proposes_only": True,
            "mutates_workflow": False,
        }
