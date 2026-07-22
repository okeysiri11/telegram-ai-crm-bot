"""AI Agronomist assistant and enterprise decision support."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

ADVISORY_TYPES = ["crop", "soil", "disease", "pest", "nutrition", "harvest", "season"]
DECISION_INTENTS = ["operational", "risk", "cost", "profit", "executive"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIAgronomistAssistant:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def consult(self, *, query: str, farm_id: str = "", context: dict[str, Any] | None = None) -> dict[str, Any]:
        if not query:
            raise ValidationError("query required")
        cid = _id("aa_con")
        lower = query.lower()
        topic = "general"
        for t in ADVISORY_TYPES:
            if t in lower:
                topic = t
                break
        advice = {
            "crop": "Favor resilient varieties; stagger planting windows.",
            "soil": "Sample zones; correct pH before nutrient push.",
            "disease": "Scout wet canopies; apply preventive fungicide if humidity >75%.",
            "pest": "Threshold-based treatment; prefer biocontrol first.",
            "nutrition": "Split N applications; match to growth stage.",
            "harvest": "Target moisture 13–14%; prioritize high-risk fields first.",
            "season": "Align fieldwork with forecast dry windows.",
            "general": "Clarify crop, growth stage, and field conditions for sharper advice.",
        }[topic]
        return self.store.aa_consultations.save(
            cid,
            {
                "consultation_id": cid,
                "query": query,
                "farm_id": farm_id,
                "topic": topic,
                "advice": advice,
                "context": context or {},
                "at": _now(),
            },
        )

    def advise(self, *, advisory_type: str, farm_id: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        if advisory_type not in ADVISORY_TYPES:
            raise ValidationError(f"advisory_type must be one of {ADVISORY_TYPES}")
        aid = _id("aa_adv")
        recommendations = {
            "crop": ["select_variety", "adjust_density"],
            "soil": ["lime_if_acidic", "organic_matter_boost"],
            "disease": ["scout", "treat_hotspots"],
            "pest": ["monitor_traps", "spot_spray"],
            "nutrition": ["tissue_test", "variable_rate_n"],
            "harvest": ["schedule_combine", "check_moisture"],
            "season": ["build_calendar", "reserve_contractors"],
        }[advisory_type]
        return self.store.aa_advisories.save(
            aid,
            {
                "advisory_id": aid,
                "advisory_type": advisory_type,
                "farm_id": farm_id,
                "recommendations": recommendations,
                "details": details or {},
                "priority": "high" if advisory_type in ("disease", "pest", "harvest") else "medium",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "consultations": self.store.aa_consultations.count(),
            "advisories": self.store.aa_advisories.count(),
        }


class DecisionSupport:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def decide(
        self,
        *,
        intent: str,
        farm_id: str,
        options: list[str] | None = None,
        risk_score: float = 0.4,
        cost: float = 0.0,
        profit: float = 0.0,
    ) -> dict[str, Any]:
        if intent not in DECISION_INTENTS:
            raise ValidationError(f"intent must be one of {DECISION_INTENTS}")
        opts = options or ["option_a", "option_b"]
        if intent == "risk":
            chosen = opts[0] if risk_score < 0.5 else opts[-1]
            rationale = "prefer lower exposure"
        elif intent == "cost":
            chosen = opts[0]
            rationale = "minimize spend"
        elif intent == "profit":
            chosen = opts[-1] if profit >= cost else opts[0]
            rationale = "maximize margin"
        elif intent == "executive":
            chosen = opts[0]
            rationale = "align with KPI targets"
        else:
            chosen = opts[0]
            rationale = "operational priority"
        did = _id("aa_dec")
        return self.store.aa_decisions.save(
            did,
            {
                "decision_id": did,
                "intent": intent,
                "farm_id": farm_id,
                "options": opts,
                "chosen": chosen,
                "rationale": rationale,
                "risk_score": float(risk_score),
                "cost": float(cost),
                "profit": float(profit),
                "at": _now(),
            },
        )

    def scenario(self, *, farm_id: str, name: str, assumptions: dict[str, Any] | None = None) -> dict[str, Any]:
        if not name:
            raise ValidationError("scenario name required")
        assump = assumptions or {}
        yield_delta = float(assump.get("yield_delta_pct", 0) or 0)
        cost_delta = float(assump.get("cost_delta_pct", 0) or 0)
        sid = _id("aa_scn")
        return self.store.aa_scenarios.save(
            sid,
            {
                "scenario_id": sid,
                "farm_id": farm_id,
                "name": name,
                "assumptions": assump,
                "projected_margin_index": round(1.0 + yield_delta / 100 - cost_delta / 100, 3),
                "at": _now(),
            },
        )

    def recommend(self, *, farm_id: str, focus: str = "operations") -> dict[str, Any]:
        rid = _id("aa_rec")
        actions = {
            "operations": ["prioritize_irrigation", "schedule_scouting"],
            "risk": ["hedge_price", "activate_insurance_review"],
            "cost": ["renegotiate_inputs", "idle_low_utilization_assets"],
            "profit": ["shift_to_high_margin_crop", "advance_sales_contract"],
            "executive": ["approve_capex", "review_business_health"],
        }.get(focus, ["review_plan"])
        return self.store.aa_recommendations.save(
            rid,
            {
                "recommendation_id": rid,
                "farm_id": farm_id,
                "focus": focus,
                "actions": actions,
                "prioritized": True,
                "at": _now(),
            },
        )

    def prioritize(self, *, farm_id: str, tasks: list[str]) -> dict[str, Any]:
        if not tasks:
            raise ValidationError("tasks required")
        pid = _id("aa_pri")
        ranked = list(tasks)
        # Simple heuristic: irrigation/disease first
        ranked.sort(key=lambda t: 0 if any(k in t.lower() for k in ("irrig", "disease", "harvest")) else 1)
        return self.store.aa_priorities.save(
            pid,
            {"priority_id": pid, "farm_id": farm_id, "ranked_tasks": ranked, "at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {
            "decisions": self.store.aa_decisions.count(),
            "scenarios": self.store.aa_scenarios.count(),
            "recommendations": self.store.aa_recommendations.count(),
        }
