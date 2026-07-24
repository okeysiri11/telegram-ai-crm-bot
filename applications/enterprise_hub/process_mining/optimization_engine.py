from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"



from applications.enterprise_hub.process_mining.models import OPTIMIZATION_ACTIONS


class OptimizationEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def optimize(self, *, process_id: str, bottleneck_id: str | None = None) -> dict[str, Any]:
        process = self.store.epm_processes.get(process_id)
        if not process:
            raise NotFoundError(f"process not found: {process_id}")
        suggestions = []
        steps = process.get("steps") or []
        if len(steps) > 5:
            suggestions.append({"action": "remove_step", "target": steps[1], "effect": "reduce cycle time"})
        suggestions.append({"action": "merge_approvals", "target": "approve", "effect": "cut wait time"})
        suggestions.append({"action": "automate_checks", "target": "validate", "effect": "raise automation %"})
        if len(steps) >= 3:
            suggestions.append({"action": "reorder_steps", "target": f"{steps[0]}->{steps[1]}", "effect": "parallelize"})
        suggestions.append({"action": "rebalance_load", "target": "approve", "effect": "reduce overload"})
        suggestions.append({"action": "deploy_ai_agent", "target": "validate", "effect": "auto-triage"})
        for s in suggestions:
            if s["action"] not in OPTIMIZATION_ACTIONS:
                raise ValidationError(f"invalid action: {s['action']}")
        oid = _id("epm_opt")
        return self.store.epm_optimizations.save(
            oid,
            {
                "optimization_id": oid,
                "process_id": process_id,
                "bottleneck_id": bottleneck_id,
                "suggestions": suggestions,
                "expected_effect": {
                    "duration_reduction_pct": 18,
                    "cost_reduction_pct": 12,
                    "automation_gain_pct": 15,
                },
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"optimizations": len(self.store.epm_optimizations.list_all())}
