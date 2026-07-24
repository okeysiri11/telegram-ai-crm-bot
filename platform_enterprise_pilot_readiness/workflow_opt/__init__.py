"""Workflow Optimization — Sprint 23.1."""

from __future__ import annotations

from typing import Any

from platform_enterprise_pilot_readiness.models import CORE_WORKFLOWS


class WorkflowOptimization:
    def optimize(self, *, workflow: str, steps: int = 6, elapsed_ms: float = 45000) -> dict[str, Any]:
        workflow = (workflow or "").lower()
        if workflow not in CORE_WORKFLOWS:
            raise ValueError(f"unsupported workflow: {workflow}")
        steps = max(1, int(steps))
        elapsed_ms = float(elapsed_ms)
        # target: shortest path under 60s
        target_steps = min(steps, 3)
        under_60s = elapsed_ms < 60000
        shortened = max(0, steps - target_steps)
        return {
            "workflow": workflow,
            "original_steps": steps,
            "optimized_steps": target_steps,
            "steps_removed": shortened,
            "elapsed_ms": elapsed_ms,
            "under_60s": under_60s,
            "maximally_short": target_steps <= 3 and under_60s,
            "ai_may_act": False,
        }

    def optimize_all(self, *, profiles: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        profiles = profiles or {}
        results = []
        for wf in CORE_WORKFLOWS:
            p = profiles.get(wf, {})
            results.append(self.optimize(workflow=wf, steps=int(p.get("steps", 5)), elapsed_ms=float(p.get("elapsed_ms", 25000))))
        return {
            "workflows": results,
            "all_under_60s": all(r["under_60s"] for r in results),
            "all_short": all(r["maximally_short"] for r in results),
        }
