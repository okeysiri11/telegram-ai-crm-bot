"""AI Port Director assistant and enterprise decision support."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

ADVISORY_TYPES = ["port", "terminal", "cargo", "fleet", "logistics", "executive"]
NL_INTENTS = ["status", "advise", "optimize", "schedule", "escalate"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIPortDirector:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def ask(self, *, prompt: str, context: str = "port") -> dict[str, Any]:
        if not prompt:
            raise ValidationError("prompt required")
        aid = _id("ad_ask")
        return self.store.ad_assistant.save(
            aid,
            {
                "assistant_id": aid,
                "prompt": prompt,
                "context": context,
                "response": f"AI Port Director recommends reviewing {context} operations for: {prompt[:120]}",
                "confidence": 0.9,
                "at": _now(),
            },
        )

    def natural_language(self, *, utterance: str, intent: str = "status") -> dict[str, Any]:
        if not utterance:
            raise ValidationError("utterance required")
        if intent not in NL_INTENTS:
            raise ValidationError(f"intent must be one of {NL_INTENTS}")
        nid = _id("ad_nl")
        return self.store.ad_nl_ops.save(
            nid,
            {
                "nl_id": nid,
                "utterance": utterance,
                "intent": intent,
                "parsed_action": intent,
                "at": _now(),
            },
        )

    def advise(self, *, advisory_type: str, subject: str, recommendation: str = "") -> dict[str, Any]:
        if advisory_type not in ADVISORY_TYPES:
            raise ValidationError(f"advisory_type must be one of {ADVISORY_TYPES}")
        if not subject:
            raise ValidationError("subject required")
        aid = _id("ad_adv")
        return self.store.ad_advisories.save(
            aid,
            {
                "advisory_id": aid,
                "advisory_type": advisory_type,
                "subject": subject,
                "recommendation": recommendation or f"Optimize {advisory_type} for {subject}",
                "priority": "medium",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "assistant_sessions": self.store.ad_assistant.count(),
            "nl_ops": self.store.ad_nl_ops.count(),
            "advisories": self.store.ad_advisories.count(),
        }


class DecisionSupport:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def decide(self, *, topic: str, options: list[str] | None = None) -> dict[str, Any]:
        if not topic:
            raise ValidationError("decision topic required")
        opts = options or ["proceed", "defer", "escalate"]
        did = _id("ad_dec")
        return self.store.ad_decisions.save(
            did,
            {
                "decision_id": did,
                "topic": topic,
                "options": opts,
                "selected": opts[0],
                "rationale": f"Selected {opts[0]} for {topic}",
                "at": _now(),
            },
        )

    def scenario(self, *, name: str, assumptions: dict[str, Any] | None = None) -> dict[str, Any]:
        if not name:
            raise ValidationError("scenario name required")
        sid = _id("ad_scn")
        return self.store.ad_scenarios.save(
            sid,
            {
                "scenario_id": sid,
                "name": name,
                "assumptions": assumptions or {},
                "outcome_score": 0.78,
                "at": _now(),
            },
        )

    def recommend(self, *, domain: str, action: str) -> dict[str, Any]:
        if not domain or not action:
            raise ValidationError("domain and action required")
        rid = _id("ad_rec")
        return self.store.ad_recommendations.save(
            rid,
            {
                "recommendation_id": rid,
                "domain": domain,
                "action": action,
                "impact": "positive",
                "at": _now(),
            },
        )

    def allocate_resources(self, *, resource: str, quantity: float, target: str) -> dict[str, Any]:
        if not resource:
            raise ValidationError("resource required")
        aid = _id("ad_alloc")
        return self.store.ad_allocations.save(
            aid,
            {
                "allocation_id": aid,
                "resource": resource,
                "quantity": float(quantity),
                "target": target,
                "at": _now(),
            },
        )

    def set_priority(self, *, item_ref: str, priority: str = "high") -> dict[str, Any]:
        if priority not in ("low", "medium", "high", "critical"):
            raise ValidationError("priority must be low|medium|high|critical")
        pid = _id("ad_prio")
        return self.store.ad_priorities.save(
            pid,
            {
                "priority_id": pid,
                "item_ref": item_ref,
                "priority": priority,
                "at": _now(),
            },
        )

    def optimize_cost(self, *, scope: str, baseline: float) -> dict[str, Any]:
        oid = _id("ad_cost")
        return self.store.ad_cost_opts.save(
            oid,
            {
                "optimization_id": oid,
                "scope": scope,
                "baseline": float(baseline),
                "optimized": round(float(baseline) * 0.91, 2),
                "at": _now(),
            },
        )

    def profitability(self, *, segment: str, revenue: float, cost: float) -> dict[str, Any]:
        pid = _id("ad_prof")
        rev, cst = float(revenue), float(cost)
        return self.store.ad_profitability.save(
            pid,
            {
                "analysis_id": pid,
                "segment": segment,
                "revenue": rev,
                "cost": cst,
                "margin_pct": round(((rev - cst) / rev) * 100, 2) if rev else 0.0,
                "at": _now(),
            },
        )

    def strategic_plan(self, *, horizon: str, goals: list[str] | None = None) -> dict[str, Any]:
        sid = _id("ad_strat")
        return self.store.ad_strategy.save(
            sid,
            {
                "plan_id": sid,
                "horizon": horizon,
                "goals": goals or [],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "decisions": self.store.ad_decisions.count(),
            "scenarios": self.store.ad_scenarios.count(),
            "recommendations": self.store.ad_recommendations.count(),
        }
