"""Simulation Lab Suite — Sprint 24.4 / v7.4.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_simulation_lab.facade import SimulationLabLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SimulationLabSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = SimulationLabLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = SimulationLabLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("esl_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.esl_bootstraps.save(bid, record)
        sid = full["scenario"]["scenario_id"]
        self.store.esl_scenarios.save(sid, {**full["scenario"], "created_at": _now()})
        for key, attr, prefix in (
            ("what_if", "esl_what_ifs", "esl_wi"),
            ("simulation", "esl_runs", "esl_run"),
            ("impacts", "esl_impacts", "esl_imp"),
            ("scenarios", "esl_multi", "esl_ms"),
            ("comparison", "esl_comparisons", "esl_cmp"),
            ("debate", "esl_debates", "esl_deb"),
            ("history", "esl_history", "esl_hist"),
            ("owner", "esl_owner", "esl_own"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, **full[key], "created_at": _now()})
        record["scenario_id"] = sid
        self.store.esl_bootstraps.save(bid, record)
        return record

    def create_scenario(self, **kwargs: Any) -> dict[str, Any]:
        try:
            scenario = self.library.registry.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.esl_scenarios.save(scenario["scenario_id"], {**scenario, "created_at": _now()})
        return scenario

    def what_if(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.what_if.analyze(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("esl_wi")
        record = {"what_if_id": rid, **result, "created_at": _now()}
        self.store.esl_what_ifs.save(rid, record)
        return record

    def simulate(self, *, scenario_id: str, question: str | None = None, intensity: float = 1.0, baselines: dict[str, float] | None = None) -> dict[str, Any]:
        scenario = self.store.esl_scenarios.get(scenario_id)
        if not scenario:
            raise NotFoundError(f"scenario not found: {scenario_id}")
        deltas = {}
        what = None
        if question:
            try:
                what = self.library.what_if.analyze(question=question, intensity=intensity)
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc
            deltas = what["domain_deltas"]
        # optional PIN enrichment
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "predictive_intelligence") and question:
                what = what or {}
                what["predictive_hint"] = True
        except Exception:
            pass
        sim = self.library.engine.run_bundle(changes=deltas, baselines=baselines)
        impacts = self.library.impact.analyze(deltas=deltas)
        multi = self.library.multi_scenario.expand(
            baseline=next((r["projected"] for r in sim["results"] if r["domain"] == "finance"), 100.0),
            domain="finance",
        )
        resources = self.library.resources.calculate(
            staff_delta=deltas.get("workforce", 0),
            sales_delta=deltas.get("sales", 0),
        )
        risks = self.library.risk_sim.assess(impact_risks=impacts["impacts"].get("risks", 0.2), intensity=intensity)
        debate = self.library.debate.debate(scenario_name=scenario.get("name", scenario_id), impacts=impacts["impacts"])
        # council touch if available
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "enterprise_ai_orchestrator"):
                debate["orchestrator_available"] = True
        except Exception:
            pass
        run_id = _id("esl_run")
        updated = self.library.registry.record_run(scenario, run_id=run_id, result_summary="sandbox_complete")
        self.store.esl_scenarios.save(scenario_id, {**updated, "updated_at": _now()})
        hist = self.library.history.save(scenario_id=scenario_id, results={"impacts": impacts, "risks": risks})
        hid = _id("esl_hist")
        self.store.esl_history.save(hid, {"history_id": hid, **hist, "created_at": _now()})
        record = {
            "run_id": run_id,
            "scenario_id": scenario_id,
            "what_if": what,
            "simulation": sim,
            "impacts": impacts,
            "multi_scenarios": multi,
            "resources": resources,
            "risks": risks,
            "debate": debate,
            "sandbox": True,
            "mutates_production": False,
            "ai_may_act": False,
            "created_at": _now(),
        }
        self.store.esl_runs.save(run_id, record)
        iid = _id("esl_imp")
        self.store.esl_impacts.save(iid, {"impact_id": iid, **impacts, "run_id": run_id})
        did = _id("esl_deb")
        self.store.esl_debates.save(did, {"debate_id": did, **debate, "run_id": run_id})
        return record

    def compare(self, *, options: list[dict[str, Any]]) -> dict[str, Any]:
        try:
            result = self.library.comparator.compare(options=options)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("esl_cmp")
        record = {"comparison_id": rid, **result, "created_at": _now()}
        self.store.esl_comparisons.save(rid, record)
        return record

    def owner_decide(self, **kwargs: Any) -> dict[str, Any]:
        try:
            result = self.library.owner.decide(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        scenario_id = kwargs.get("scenario_id", "")
        if scenario_id and not self.store.esl_scenarios.get(scenario_id):
            raise NotFoundError(f"scenario not found: {scenario_id}")
        oid = _id("esl_own")
        record = {"owner_id": oid, **result, "created_at": _now()}
        self.store.esl_owner.save(oid, record)
        if result.get("approved") and scenario_id:
            sc = dict(self.store.esl_scenarios.get(scenario_id))
            sc["status"] = "owner_approved_pending_deploy"
            sc["owner_decision"] = result
            self.store.esl_scenarios.save(scenario_id, sc)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.esl_bootstraps.list_all()),
            "scenarios": len(self.store.esl_scenarios.list_all()),
            "runs": len(self.store.esl_runs.list_all()),
            "sandbox": True,
        }


simulation_lab = SimulationLabSuite()
