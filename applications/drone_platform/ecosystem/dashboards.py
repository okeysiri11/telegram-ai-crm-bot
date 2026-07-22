"""Executive and domain dashboards (Sprint 11.10)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutiveDashboards:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def executive(self) -> dict[str, Any]:
        return {
            "type": "executive_dashboard",
            "kpis": {
                "modules": len(self.store.ecosystem_registry.list_all()),
                "twins": len(self.store.unified_twins.list_all()),
                "lifecycles": len(self.store.aircraft_lifecycles_eco.list_all()),
                "missions": len(self.store.ops_missions.list_all()),
                "fleet": len(self.store.fleet_aircraft.list_all()) + len(self.store.cloud_fleets.list_all()),
                "certification": len(self.store.certification_runs.list_all()),
            },
            "at": _now(),
        }

    def engineering(self) -> dict[str, Any]:
        return {"type": "engineering_dashboard", "projects": len(self.store.pcb_projects.list_all()) + len(self.store.cad_assemblies.list_all()), "at": _now()}

    def manufacturing(self) -> dict[str, Any]:
        return {"type": "manufacturing_dashboard", "orders": len(self.store.production_orders.list_all()), "assemblies": len(self.store.assemblies.list_all()), "at": _now()}

    def mission(self) -> dict[str, Any]:
        return {"type": "mission_dashboard", "ops_missions": len(self.store.ops_missions.list_all()), "swarm": len(self.store.swarm_missions.list_all()), "at": _now()}

    def fleet(self) -> dict[str, Any]:
        return {"type": "fleet_dashboard", "aircraft": len(self.store.fleet_aircraft.list_all()), "cloud_fleets": len(self.store.cloud_fleets.list_all()), "at": _now()}

    def cloud(self) -> dict[str, Any]:
        return {"type": "cloud_dashboard", "nodes": len(self.store.cloud_nodes.list_all()), "incidents": len(self.store.cloud_incidents.list_all()), "at": _now()}

    def ai(self) -> dict[str, Any]:
        return {"type": "ai_dashboard", "agents": 10, "events": len(self.store.ecosystem_events.list_all()), "at": _now()}

    def financial(self) -> dict[str, Any]:
        return {"type": "financial_dashboard", "metrics": {"production_cost_index": 1.0, "fleet_utilization": 0.72, "maintenance_budget_pct": 0.15}, "at": _now()}

    def system_health(self) -> dict[str, Any]:
        return {"type": "system_health_dashboard", "snapshots": len(self.store.health_snapshots.list_all()), "recoveries": len(self.store.recovery_events.list_all()), "at": _now()}

    def all_dashboards(self) -> dict[str, Any]:
        return {
            "executive": self.executive(),
            "engineering": self.engineering(),
            "manufacturing": self.manufacturing(),
            "mission": self.mission(),
            "fleet": self.fleet(),
            "cloud": self.cloud(),
            "ai": self.ai(),
            "financial": self.financial(),
            "system_health": self.system_health(),
        }

    def status(self) -> dict[str, Any]:
        return {"executive_dashboards": "1.0", "views": 9, "ready": True}


executive_dashboards = ExecutiveDashboards()
