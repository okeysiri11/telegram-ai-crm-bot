"""Recommendation Engine — AI action proposals from simulation results."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.simulation_engine.models import RECOMMENDATION_ACTIONS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class RecommendationEngine:
    """Form AI recommendations from scenarios, risks, and optimizations."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def generate(
        self,
        *,
        scenario_id: str | None = None,
        decision_id: str | None = None,
        risk_id: str | None = None,
        actions: list[str] | None = None,
    ) -> dict[str, Any]:
        proposed = list(actions or [])
        if not proposed:
            proposed = self._infer_actions(scenario_id=scenario_id, risk_id=risk_id)
        for a in proposed:
            if a not in RECOMMENDATION_ACTIONS:
                raise ValidationError(f"invalid recommendation action: {a}")
        items = [
            {
                "action": a,
                "priority": idx + 1,
                "rationale": self._rationale(a),
                "expected_effect": self._effect(a),
            }
            for idx, a in enumerate(proposed)
        ]
        rid = _id("esi_ai_rec")
        return self.store.esi_recommendations.save(
            rid,
            {
                "recommendation_id": rid,
                "scenario_id": scenario_id,
                "decision_id": decision_id,
                "risk_id": risk_id,
                "actions": items,
                "top_action": items[0]["action"] if items else None,
                "at": _now(),
            },
        )

    def _infer_actions(self, *, scenario_id: str | None, risk_id: str | None) -> list[str]:
        actions: list[str] = []
        scn = self.store.esi_scenarios.get(scenario_id) if scenario_id else None
        risk = self.store.esi_risks.get(risk_id) if risk_id else None
        kind = (scn or {}).get("kind", "")
        domain = (scn or {}).get("domain", "")
        if kind == "demand_increase" or domain == "warehouse":
            actions.append("increase_inventory")
        if kind == "resource_cost_change" or domain == "logistics":
            actions.append("reschedule_delivery")
        if domain == "hr" or "workforce" in ((risk or {}).get("critical") or []):
            actions.append("redistribute_workforce")
        if kind == "equipment_failure" or domain == "manufacturing":
            actions.extend(["change_production_schedule", "acquire_equipment"])
        if not actions:
            actions = ["increase_inventory", "redistribute_workforce", "change_production_schedule"]
        # unique preserve order
        seen: set[str] = set()
        out = []
        for a in actions:
            if a not in seen:
                seen.add(a)
                out.append(a)
        return out

    def _rationale(self, action: str) -> str:
        return {
            "increase_inventory": "Buffer stock reduces stockout risk under demand/cost shocks",
            "reschedule_delivery": "Shift inbound timing to cut cost/delay exposure",
            "redistribute_workforce": "Rebalance headcount toward bottleneck work centers",
            "change_production_schedule": "Re-sequence lines to absorb downtime and demand peaks",
            "acquire_equipment": "Add capacity where failure/utilization risk is critical",
        }.get(action, "Improve enterprise outcome based on simulation")

    def _effect(self, action: str) -> dict[str, float]:
        return {
            "increase_inventory": {"profit_delta_pct": 2.0, "risk_delta": -0.1},
            "reschedule_delivery": {"cost_delta_pct": -4.0, "risk_delta": -0.05},
            "redistribute_workforce": {"efficiency_delta_pct": 6.0, "risk_delta": -0.04},
            "change_production_schedule": {"time_delta_days": -2.0, "risk_delta": -0.08},
            "acquire_equipment": {"efficiency_delta_pct": 10.0, "cost_delta_pct": 8.0},
        }.get(action, {"profit_delta_pct": 1.0})

    def status(self) -> dict[str, Any]:
        items = self.store.esi_recommendations.list_all()
        return {"recommendations": len(items), "latest_top": items[-1].get("top_action") if items else None}
