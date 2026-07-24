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



from applications.enterprise_hub.simulation_engine.models import SCENARIO_DOMAINS, SCENARIO_KINDS


class ScenarioEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def create(
        self,
        *,
        domain: str,
        question: str,
        kind: str = "what_if",
        parameters: dict[str, Any] | None = None,
        twin_context_id: str | None = None,
    ) -> dict[str, Any]:
        if domain not in SCENARIO_DOMAINS:
            raise ValidationError(f"invalid domain: {domain}")
        if kind not in SCENARIO_KINDS:
            raise ValidationError(f"invalid kind: {kind}")
        if not question:
            raise ValidationError("question is required")
        params = dict(parameters or {})
        sid = _id("esi_scn")
        # heuristic projected impact
        shock = float(params.get("shock_pct", params.get("demand_pct", params.get("cost_pct", 10))))
        impact = {
            "profit_delta_pct": round(-shock * 0.4 if "cost" in kind or "failure" in kind else shock * 0.35, 2),
            "cost_delta_pct": round(shock * 0.5 if "cost" in kind or "failure" in kind else -shock * 0.1, 2),
            "risk_score": min(1.0, round(0.2 + abs(shock) / 100, 3)),
            "time_delta_days": int(abs(shock) / 5) if "failure" in kind else int(abs(shock) / 10),
        }
        return self.store.esi_scenarios.save(
            sid,
            {
                "scenario_id": sid,
                "domain": domain,
                "kind": kind,
                "question": question,
                "parameters": params,
                "twin_context_id": twin_context_id,
                "projected_impact": impact,
                "status": "draft",
                "created_at": _now(),
            },
        )

    def run(self, *, scenario_id: str) -> dict[str, Any]:
        scn = self.store.esi_scenarios.get(scenario_id)
        if not scn:
            raise NotFoundError(f"scenario not found: {scenario_id}")
        scn["status"] = "completed"
        scn["completed_at"] = _now()
        self.store.esi_scenarios.save(scenario_id, scn)
        rid = _id("esi_srun")
        return self.store.esi_scenario_runs.save(
            rid,
            {
                "run_id": rid,
                "scenario_id": scenario_id,
                "impact": scn.get("projected_impact"),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        items = self.store.esi_scenarios.list_all()
        return {"scenarios": len(items), "runs": len(self.store.esi_scenario_runs.list_all())}
