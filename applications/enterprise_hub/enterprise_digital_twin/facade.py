"""Enterprise Digital Twin 2.0 Suite — Sprint 24.5 / v7.5.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_enterprise_digital_twin.facade import EnterpriseDigitalTwinLibrary

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseDigitalTwinSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.library = EnterpriseDigitalTwinLibrary()

    def integrations(self) -> dict[str, Any]:
        return self.library.integrations.link()

    def bootstrap(self) -> dict[str, Any]:
        self.library = EnterpriseDigitalTwinLibrary()
        result = self.library.bootstrap()
        full = result.pop("full")
        bid = _id("etw_boot")
        record = {
            "bootstrap_id": bid,
            **result,
            "version": DEFAULT_CONFIG.application_version,
            "bootstrapped_at": _now(),
        }
        self.store.etw_bootstraps.save(bid, record)
        cid = full["twin"]["company_id"]
        self.store.etw_twins.save(cid, {**full["twin"], "created_at": _now()})
        for key, attr, prefix in (
            ("live", "etw_live", "etw_live"),
            ("org", "etw_org", "etw_org"),
            ("processes", "etw_processes", "etw_proc"),
            ("sync", "etw_sync", "etw_sync"),
            ("dashboard", "etw_dashboards", "etw_dash"),
            ("impact", "etw_impacts", "etw_imp"),
        ):
            rid = _id(prefix)
            getattr(self.store, attr).save(rid, {"record_id": rid, "company_id": cid, **full[key], "created_at": _now()})
        record["company_id"] = cid
        self.store.etw_bootstraps.save(bid, record)
        return record

    def create_twin(self, **kwargs: Any) -> dict[str, Any]:
        try:
            twin = self.library.registry.create(**kwargs)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        self.store.etw_twins.save(twin["company_id"], {**twin, "created_at": _now()})
        return twin

    def live_state(self, *, company_id: str, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
        twin = self.store.etw_twins.get(company_id)
        if not twin:
            raise NotFoundError(f"twin not found: {company_id}")
        # enrich from modules when available
        enriched = dict(metrics or {})
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "operations_center"):
                enriched.setdefault("services_status", "ok")
            if hasattr(enterprise_hub, "commerce_core"):
                enriched.setdefault("ai_status", "ok")
        except Exception:
            pass
        live = self.library.live_state.snapshot(metrics=enriched)
        self.library.time_machine.save_snapshot(company_id=company_id, label="1h", state=live)
        rid = _id("etw_live")
        record = {"live_id": rid, "company_id": company_id, **live, "created_at": _now()}
        self.store.etw_live.save(rid, record)
        twin = self.library.registry.record_change(twin, event="live_refresh")
        self.store.etw_twins.save(company_id, twin)
        return record

    def organization_map(self, *, company_id: str) -> dict[str, Any]:
        twin = self.store.etw_twins.get(company_id)
        if not twin:
            raise NotFoundError(f"twin not found: {company_id}")
        org = self.library.org_map.render(twin=twin)
        rid = _id("etw_org")
        record = {"org_id": rid, **org, "created_at": _now()}
        self.store.etw_org.save(rid, record)
        return record

    def processes(self, *, company_id: str, processes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        twin = self.store.etw_twins.get(company_id)
        if not twin:
            raise NotFoundError(f"twin not found: {company_id}")
        procs_list = processes if processes is not None else list(twin.get("active_processes") or [])
        # pull from workflow intelligence runs lightly
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "workflow_intelligence") and not procs_list:
                runs = enterprise_hub.store.wfi_runs.list_all()[:5]
                procs_list = [{"id": r.get("run_id"), "status": "completed" if r.get("executed") else "awaiting_approval"} for r in runs]
        except Exception:
            pass
        view = self.library.process_viz.render(processes=procs_list)
        rid = _id("etw_proc")
        record = {"process_view_id": rid, "company_id": company_id, **view, "created_at": _now()}
        self.store.etw_processes.save(rid, record)
        return record

    def sync_twin(self, *, company_id: str) -> dict[str, Any]:
        twin = self.store.etw_twins.get(company_id)
        if not twin:
            raise NotFoundError(f"twin not found: {company_id}")
        sources: dict[str, Any] = {}
        try:
            from applications.enterprise_hub import enterprise_hub

            for name in (
                "commerce_core",
                "ai_marketing_os",
                "communications_hub",
                "workflow_intelligence",
                "enterprise_knowledge_graph",
                "predictive_intelligence",
                "simulation_lab",
                "operations_center",
            ):
                if hasattr(enterprise_hub, name):
                    sources[name if name != "commerce_core" else "commerce"] = {"linked": True}
                    if name == "ai_marketing_os":
                        sources["marketing"] = {"linked": True}
                    if name == "communications_hub":
                        sources["communications"] = {"linked": True}
                    if name == "workflow_intelligence":
                        sources["workflow"] = {"linked": True}
                    if name == "enterprise_knowledge_graph":
                        sources["enterprise_knowledge_graph"] = {"linked": True}
                    if name == "predictive_intelligence":
                        sources["predictive_intelligence"] = {"linked": True}
                    if name == "simulation_lab":
                        sources["simulation_lab"] = {"linked": True}
                    if name == "operations_center":
                        sources["operations_center"] = {"linked": True}
            sources.setdefault("crm", {"linked": True})
        except Exception:
            pass
        result = self.library.sync.sync(sources=sources)
        rid = _id("etw_sync")
        record = {"sync_id": rid, "company_id": company_id, **result, "created_at": _now()}
        self.store.etw_sync.save(rid, record)
        twin = self.library.registry.record_change(twin, event="sync", details={"all_ok": result["all_ok"]})
        self.store.etw_twins.save(company_id, twin)
        return record

    def time_machine(self, *, company_id: str, preset: str = "1h", custom_label: str = "") -> dict[str, Any]:
        if not self.store.etw_twins.get(company_id):
            raise NotFoundError(f"twin not found: {company_id}")
        # ensure snapshots exist
        live_rows = [x for x in self.store.etw_live.list_all() if x.get("company_id") == company_id]
        if live_rows:
            self.library.time_machine.save_snapshot(company_id=company_id, label=preset if preset != "custom" else custom_label or "custom", state=live_rows[-1])
        try:
            result = self.library.time_machine.recall(company_id=company_id, preset=preset, custom_label=custom_label)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        rid = _id("etw_tm")
        record = {"time_id": rid, **result, "created_at": _now()}
        self.store.etw_timemachine.save(rid, record)
        return record

    def change_impact(self, **kwargs: Any) -> dict[str, Any]:
        result = self.library.change_impact.view(**kwargs)
        rid = _id("etw_imp")
        record = {"impact_id": rid, **result, "created_at": _now()}
        self.store.etw_impacts.save(rid, record)
        return record

    def twin_state(self, *, company_id: str) -> dict[str, Any]:
        """Twin API — unified state for internal services."""
        twin = self.store.etw_twins.get(company_id)
        if not twin:
            raise NotFoundError(f"twin not found: {company_id}")
        live = self.live_state(company_id=company_id, metrics={})
        org = self.organization_map(company_id=company_id)
        procs = self.processes(company_id=company_id)
        sync = self.sync_twin(company_id=company_id)
        ai = self.library.ai_monitor.monitor(
            agents=[{"id": "ai", "status": twin.get("ai_state", {}).get("status", "idle")}],
            pending=[{"id": p["id"]} for p in twin.get("active_processes", []) if p.get("status") == "awaiting_approval"],
        )
        resources = self.library.resources.monitor(resources=twin.get("resources"))
        return {
            "company_id": company_id,
            "twin": twin,
            "live": live,
            "organization": org,
            "processes": procs,
            "resources": resources,
            "ai": ai,
            "sync": sync,
            "api": "enterprise-etw",
            "version": "2.0",
            "source_for": ["predictive_intelligence", "simulation_lab", "enterprise_ai_orchestrator"],
        }

    def owner_dashboard(self, *, company_id: str) -> dict[str, Any]:
        state = self.twin_state(company_id=company_id)
        forecasts = []
        simulations = []
        try:
            from applications.enterprise_hub import enterprise_hub

            if hasattr(enterprise_hub, "predictive_intelligence"):
                forecasts = enterprise_hub.store.pin_forecasts.list_all()[-3:]
            if hasattr(enterprise_hub, "simulation_lab"):
                simulations = enterprise_hub.store.esl_runs.list_all()[-3:]
        except Exception:
            pass
        dash = self.library.dashboard.render(
            live=state["live"],
            processes=state["processes"],
            warnings=["awaiting_approval"] if state["processes"].get("awaiting_approval") else [],
            forecasts=forecasts,
            recommendations=["use_twin_as_source_of_truth"],
            simulations=simulations,
        )
        rid = _id("etw_dash")
        record = {"dashboard_id": rid, "company_id": company_id, **dash, "created_at": _now()}
        self.store.etw_dashboards.save(rid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {
            "library": self.library.status(),
            "bootstraps": len(self.store.etw_bootstraps.list_all()),
            "twins": len(self.store.etw_twins.list_all()),
            "version": "2.0",
        }


enterprise_digital_twin = EnterpriseDigitalTwinSuite()
