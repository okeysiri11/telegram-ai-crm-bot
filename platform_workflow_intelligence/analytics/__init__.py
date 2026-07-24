"""Workflow Analytics — Sprint 24.1."""

from __future__ import annotations

from typing import Any


class WorkflowAnalytics:
    def summarize(self, *, runs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        runs = list(runs or [])
        durations = [float(r.get("duration_ms", 0)) for r in runs]
        successes = sum(1 for r in runs if r.get("success") or r.get("status") == "completed")
        errors = [r.get("error") for r in runs if r.get("error")]
        stops = [r.get("stop_reason") for r in runs if r.get("stop_reason")]
        cost = sum(float(r.get("cost", 0)) for r in runs)
        success_rate = (successes / len(runs)) if runs else 1.0
        return {
            "run_count": len(runs),
            "avg_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0.0,
            "success_rate": round(success_rate, 3),
            "success_rate_95pct": success_rate >= 0.95,
            "errors": errors,
            "stop_reasons": stops,
            "process_cost": cost,
            "ai_recommendations": [r.get("ai_tip") for r in runs if r.get("ai_tip")],
        }
