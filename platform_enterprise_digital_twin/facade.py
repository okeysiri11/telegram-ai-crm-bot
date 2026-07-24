"""Enterprise Digital Twin 2.0 library facade — Sprint 24.5."""

from __future__ import annotations

from typing import Any

from platform_enterprise_digital_twin.ai_monitor import AIActivityMonitor
from platform_enterprise_digital_twin.change_impact import ChangeImpactView
from platform_enterprise_digital_twin.dashboard import OwnerTwinDashboard
from platform_enterprise_digital_twin.integrations import TwinIntegrations
from platform_enterprise_digital_twin.live_state import LiveStateEngine
from platform_enterprise_digital_twin.models import PRINCIPLES
from platform_enterprise_digital_twin.org_map import OrganizationMap
from platform_enterprise_digital_twin.process_viz import ProcessVisualization
from platform_enterprise_digital_twin.registry import TwinRegistry
from platform_enterprise_digital_twin.resources import ResourceMonitor
from platform_enterprise_digital_twin.sync import TwinSynchronization
from platform_enterprise_digital_twin.time_machine import TimeMachine


class EnterpriseDigitalTwinLibrary:
    def __init__(self) -> None:
        self.registry = TwinRegistry()
        self.live_state = LiveStateEngine()
        self.org_map = OrganizationMap()
        self.process_viz = ProcessVisualization()
        self.resources = ResourceMonitor()
        self.ai_monitor = AIActivityMonitor()
        self.time_machine = TimeMachine()
        self.change_impact = ChangeImpactView()
        self.sync = TwinSynchronization()
        self.dashboard = OwnerTwinDashboard()
        self.integrations = TwinIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        twin = self.registry.create(
            company_id="co_twin",
            branches=[{"branch_id": "b1", "name": "Main"}],
            employees=[{"employee_id": "e1", "name": "Anna", "team": "masters", "branch_id": "b1"}],
            customers=[{"customer_id": "c1", "name": "Client"}],
        )
        live = self.live_state.snapshot(
            metrics={
                "customers": 12,
                "active_appointments": 4,
                "sales": 1500,
                "staff_load": 0.7,
                "inventory": 80,
                "campaigns": 2,
                "finance": 9000,
            }
        )
        twin["resources"] = {"personnel": 5, "equipment": 3, "materials": 80, "premises": 1, "finance": 9000, "compute": 2}
        twin["active_processes"] = [
            {"id": "p1", "status": "running"},
            {"id": "p2", "status": "awaiting_approval"},
            {"id": "p3", "status": "queued"},
        ]
        twin["ai_state"] = {"agents": 3, "status": "active"}
        org = self.org_map.render(twin=twin)
        procs = self.process_viz.render(processes=twin["active_processes"])
        res = self.resources.monitor(resources=twin["resources"])
        ai = self.ai_monitor.monitor(
            agents=[{"id": "ai_business", "status": "active"}],
            tasks=[{"id": "t1", "name": "forecast"}],
            recommendations=["rebook_vip"],
            pending=[{"id": "d1", "type": "owner_approval"}],
        )
        self.time_machine.save_snapshot(company_id="co_twin", label="1h", state=live)
        self.time_machine.save_snapshot(company_id="co_twin", label="1d", state=self.live_state.snapshot(metrics={"customers": 10, "sales": 1200}))
        past = self.time_machine.recall(company_id="co_twin", preset="1d")
        cmp_ = self.time_machine.compare(a=past["snapshot"], b={"state": live})
        impact = self.change_impact.view(
            changed_objects=["inventory"],
            affected_processes=["p1"],
            ai_consumers=["predictive_intelligence"],
            updated_forecasts=["revenue"],
        )
        synced = self.sync.sync(sources={"crm": {"ok": True}, "commerce": {"sales": 1500}})
        dash = self.dashboard.render(
            live=live,
            processes=procs,
            warnings=["awaiting_owner_approval"],
            forecasts=[{"domain": "revenue", "value": 10000}],
            recommendations=["rebook_vip"],
            simulations=[{"scenario": "hire_staff", "result": "positive"}],
        )
        twin = self.registry.record_change(twin, event="bootstrap_sync", details={"synced": True})
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "enterprise_digital_twin_ready": True,
            "live_state_ready": True,
            "twin_sync_ready": True,
            "twin_time_machine_ready": True,
            "realtime": True,
            "all_synced": synced["all_ok"],
            "ai_may_act": False,
            "source_for_pin_esl_eao": True,
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "twin": twin,
                "live": live,
                "org": org,
                "processes": procs,
                "resources": res,
                "ai": ai,
                "time_machine": past,
                "compare": cmp_,
                "impact": impact,
                "sync": synced,
                "dashboard": dash,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "registry",
                "live_state",
                "org_map",
                "process_viz",
                "resources",
                "ai_monitor",
                "time_machine",
                "change_impact",
                "sync",
                "dashboard",
            ],
            "principles": self.principles(),
            "version": "2.0",
        }


enterprise_digital_twin_library = EnterpriseDigitalTwinLibrary()
