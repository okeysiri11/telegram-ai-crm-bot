"""AI Business Advisor Suite facade — Sprint 22.1 / v6.2.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_ai_business_advisor.facade import AIBusinessAdvisorLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIBusinessAdvisorSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = AIBusinessAdvisorLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = AIBusinessAdvisorLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("aba_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.aba_bootstraps.save(bid, record)
        hid = _id("aba_health")
        self.store.aba_health.save(hid, {"health_id": hid, **full["health"], "analyzed_at": _now()})
        oid = _id("aba_opp")
        self.store.aba_opportunities.save(oid, {"opportunity_set_id": oid, **full["opportunities"], "detected_at": _now()})
        rid = _id("aba_rec")
        self.store.aba_recommendations.save(
            rid, {"recommendation_set_id": rid, **full["recommendations"], "generated_at": _now()}
        )
        fid = _id("aba_fc")
        self.store.aba_forecasts.save(fid, {"forecast_id": fid, **full["forecasts"], "generated_at": _now()})
        brief_id = _id("aba_brief")
        self.store.aba_briefs.save(brief_id, {"brief_id": brief_id, **full["brief"], "generated_at": _now()})
        for handoff in full["product_intelligence_handoffs"]:
            eid = _id("aba_epi")
            self.store.aba_handoffs.save(eid, {"handoff_id": eid, **handoff, "created_at": _now()})
        record["brief_id"] = brief_id
        record["health_id"] = hid
        record["recommendation_set_id"] = rid
        self.store.aba_bootstraps.save(bid, record)
        return record

    def analyze_health(self, *, industry: str = "generic", snapshot: dict[str, float] | None = None) -> dict[str, Any]:
        try:
            result = self.library.health.analyze(industry=industry, snapshot=snapshot)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        hid = _id("aba_health")
        record = {"health_id": hid, **result, "analyzed_at": _now()}
        self.store.aba_health.save(hid, record)
        return record

    def run_daily(self, *, industry: str = "generic", snapshot: dict[str, float] | None = None) -> dict[str, Any]:
        try:
            cycle = self.library.run_cycle(industry=industry, snapshot=snapshot)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        brief_id = _id("aba_brief")
        record = {
            "brief_id": brief_id,
            **cycle["brief"],
            "industry": industry,
            "opportunities": cycle["opportunities"]["count"],
            "recommendations": cycle["recommendations"]["count"],
            "generated_at": _now(),
        }
        self.store.aba_briefs.save(brief_id, record)
        hid = _id("aba_health")
        self.store.aba_health.save(hid, {"health_id": hid, **cycle["health"], "analyzed_at": _now()})
        rid = _id("aba_rec")
        self.store.aba_recommendations.save(
            rid, {"recommendation_set_id": rid, **cycle["recommendations"], "generated_at": _now()}
        )
        for handoff in cycle["product_intelligence_handoffs"]:
            eid = _id("aba_epi")
            self.store.aba_handoffs.save(eid, {"handoff_id": eid, "brief_id": brief_id, **handoff, "created_at": _now()})
        record["health_id"] = hid
        record["recommendation_set_id"] = rid
        self.store.aba_briefs.save(brief_id, record)
        return record

    def owner_decide(self, *, recommendation_set_id: str, decision: str, owner_id: str, notes: str = "") -> dict[str, Any]:
        recs = self.store.aba_recommendations.get(recommendation_set_id)
        if not recs:
            raise NotFoundError(f"recommendation set not found: {recommendation_set_id}")
        try:
            result = self.library.approval.decide(decision=decision, owner_id=owner_id, notes=notes)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        did = _id("aba_dec")
        record = {
            "decision_id": did,
            "recommendation_set_id": recommendation_set_id,
            **result,
            "decided_at": _now(),
        }
        self.store.aba_decisions.save(did, record)
        return record

    def latest_brief(self) -> dict[str, Any]:
        items = self.store.aba_briefs.list_all()
        if not items:
            raise NotFoundError("daily brief not found; run daily or bootstrap first")
        return items[-1]

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.aba_bootstraps.list_all()),
            "briefs": len(self.store.aba_briefs.list_all()),
            "recommendations": len(self.store.aba_recommendations.list_all()),
            "handoffs": len(self.store.aba_handoffs.list_all()),
            "decisions": len(self.store.aba_decisions.list_all()),
        }


ai_business_advisor = AIBusinessAdvisorSuite()
