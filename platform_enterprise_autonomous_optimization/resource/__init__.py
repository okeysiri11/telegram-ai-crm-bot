"""Resource Optimizer — Sprint 24.6."""

from __future__ import annotations

from typing import Any


class ResourceOptimizer:
    def analyze(self, *, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        signals = dict(signals or {})
        tips = []
        if float(signals.get("staff_idle_pct", 0)) > 0.15:
            tips.append({"target": "personnel", "action": "rebalance_shifts"})
        if float(signals.get("material_waste_pct", 0)) > 0.1:
            tips.append({"target": "materials", "action": "reduce_overstock"})
        if float(signals.get("equipment_idle_pct", 0)) > 0.2:
            tips.append({"target": "equipment", "action": "share_across_branches"})
        if float(signals.get("branch_underuse", 0)) > 0:
            tips.append({"target": "branches", "action": "shift_demand"})
        if float(signals.get("ai_overprovision", 0)) > 0:
            tips.append({"target": "ai_resources", "action": "cap_idle_agents"})
        if not tips:
            tips.append({"target": "working_time", "action": "maintain"})
        return {"tips": tips, "category": "resource"}
