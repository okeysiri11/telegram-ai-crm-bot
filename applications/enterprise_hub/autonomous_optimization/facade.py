"""Autonomous Optimization Suite — Sprint 24.6 / v7.6.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_autonomous_optimization.facade import AutonomousOptimizationLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AutonomousOptimizationSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = AutonomousOptimizationLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = AutonomousOptimizationLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("eoe_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.eoe_bootstraps.save(bid, record)
        oid = full["opportunity"]["opportunity_id"]
        self.store.eoe_opportunities.save(oid, {**full["opportunity"], "created_at": _now()})
        for key, attr, prefix in (
            ("process", "eoe_process", "eoe_proc"),
            ("council", "eoe_council", "eoe_cnc"),
            ("decision", "eoe_owner", "eoe_own"),
            ("verification", "eoe_verification", "eoe_ver"),
            ("dashboard", "eoe_dashboards", "eoe_dash"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        record["opportunity_id"] = oid
        self.store.eoe_bootstraps.save(bid, record)
        return record

    def scan(self, *, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        signals = dict(signals or {})
        # enrich lightly from twin / pin when available
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "enterprise_digital_twin"):
                signals.setdefault("from_twin", True)
            if hasattr(enterprise_hub, "predictive_intelligence"):
                signals.setdefault("from_pin", True)
        except Exception:
            pass
        process = self.library.process.analyze(signals=signals)
        resource = self.library.resource.analyze(signals=signals)
        revenue = self.library.revenue.analyze(signals=signals)
        cost = self.library.cost.analyze(signals=signals)
        cx = self.library.cx.analyze(signals=signals)
        rid = _id("eoe_scan")
        record = {
            "scan_id": rid,
            "process": process,
            "resource": resource,
            "revenue": revenue,
            "cost": cost,
            "cx": cx,
            "ai_may_act": False,
            "created_at": _now(),
        }
        self.store.eoe_scans.save(rid, record)
        return record

    def propose(self, **kwargs: Any) -> dict[str, Any]:
        try:
            opp = self.library.registry.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        scored = self.library.scoring.score(opportunity=opp)
        opp = {**opp, **scored}
        review = self.library.council.review(opportunity=opp)
        # optional EAO convene touch
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "enterprise_ai_orchestrator"):
                review["orchestrator_available"] = True
        except Exception:
            pass
        opp = self.library.registry.set_status(opp, status="awaiting_owner")
        self.store.eoe_opportunities.save(opp["opportunity_id"], {**opp, "council": review, "created_at": _now()})
        cid = _id("eoe_cnc")
        self.store.eoe_council.save(cid, {"council_id": cid, **review, "created_at": _now()})
        return {"opportunity": opp, "council": review, "pipeline": review["pipeline"], "ai_may_act": False}

    def owner_decide(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.owner.decide(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        oid = kwargs.get("opportunity_id", "")
        opp = self.store.eoe_opportunities.get(oid)
        if not opp:
            raise NotFoundError(f"opportunity not found: {oid}")
        status = result["status"]
        updated = self.library.registry.set_status(opp, status=status)
        if kwargs.get("action") == "modify" and kwargs.get("modifications"):
            updated = {**updated, **(kwargs.get("modifications") or {})}
            updated["owner_status"] = "modified"
        self.store.eoe_opportunities.save(oid, {**updated, "owner_decision": result, "updated_at": _now()})
        rid = _id("eoe_own")
        record = {"owner_id": rid, **result, "created_at": _now()}
        self.store.eoe_owner.save(rid, record)
        return record

    def verify(self, *, opportunity_id: str, expected: float, actual: float, confirmed: bool = False) -> dict[str, Any]:
        opp = self.store.eoe_opportunities.get(opportunity_id)
        if not opp:
            raise NotFoundError(f"opportunity not found: {opportunity_id}")
        result = self.library.verification.verify(expected=expected, actual=actual, confirmed=confirmed)
        if result.get("verified"):
            updated = self.library.registry.record_implementation(opp, note="verified", result=result)
            updated = self.library.registry.set_status(updated, status="verified")
            self.store.eoe_opportunities.save(opportunity_id, updated)
            # knowledge graph touch
            try:
                from applications.enterprise_hub import enterprise_hub

                if hasattr(enterprise_hub, "enterprise_knowledge_graph") and result.get("update_knowledge_graph"):
                    result["knowledge_graph_hook"] = True
            except Exception:
                pass
        rid = _id("eoe_ver")
        record = {"verification_id": rid, "opportunity_id": opportunity_id, **result, "created_at": _now()}
        self.store.eoe_verification.save(rid, record)
        return record

    def list_opportunities(self) -> dict[str, Any]:
        items = self.store.eoe_opportunities.list_all()
        ranked = sorted(items, key=lambda x: float(x.get("rank_score", 0)), reverse=True)
        return {"opportunities": ranked, "count": len(ranked), "ranked": True}

    def owner_dashboard(self) -> dict[str, Any]:
        opps = self.list_opportunities()["opportunities"][:5]
        hist = []
        for o in opps:
            hist.extend(o.get("implementation_history") or [])
        dash = self.library.dashboard.render(
            top_opportunities=opps,
            projected_savings=sum(float(o.get("business_value", 0)) * 0.2 for o in opps),
            projected_profit_growth=sum(float(o.get("business_value", 0)) for o in opps),
            council_notes=["review_top_ranked"],
            implementation_history=hist[-10:],
        )
        rid = _id("eoe_dash")
        record = {"dashboard_id": rid, **dash, "created_at": _now()}
        self.store.eoe_dashboards.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.eoe_bootstraps.list_all()),
            "opportunities": len(self.store.eoe_opportunities.list_all()),
            "autonomous_deploy": False,
        }


autonomous_optimization = AutonomousOptimizationSuite()
