"""Engineering Integration — auto-connect platform modules (Sprint 11.10)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.ecosystem.manager import MODULE_CATALOG, DroneEcosystemManager, drone_ecosystem_manager


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


INTEGRATION_MAP = {
    "engineering": ["firmware", "manufacturing", "digital_twin", "lifecycle"],
    "firmware": ["mavlink", "mission_planning", "cloud"],
    "mavlink": ["ground_control", "mission_center"],
    "mission_planning": ["mission_center", "ground_control"],
    "manufacturing": ["warehouse", "lifecycle", "engineering"],
    "warehouse": ["manufacturing", "lifecycle"],
    "lifecycle": ["engineering", "manufacturing", "cloud", "digital_twin"],
    "cloud": ["digital_twin", "mission_center", "fleet"],
    "mission_center": ["ground_control", "fleet", "cloud"],
    "ground_control": ["mission_center", "mavlink"],
    "digital_twin": ["cloud", "lifecycle", "engineering", "fleet"],
}


class EngineeringIntegration:
    def __init__(self, ecosystem: DroneEcosystemManager | None = None) -> None:
        self.ecosystem = ecosystem or drone_ecosystem_manager

    def connect_all(self) -> dict[str, Any]:
        connected = []
        for module in MODULE_CATALOG:
            self.ecosystem.register_module(module=module, version="2.0")
            connected.append(module)
        sync = self.ecosystem.cross_module_sync(modules=list(MODULE_CATALOG))
        self.ecosystem.publish_event(topic="integration.connected", payload={"modules": connected})
        return {"connected": connected, "count": len(connected), "sync_id": sync["sync_id"], "at": _now()}

    def graph(self) -> dict[str, Any]:
        return {"type": "integration_graph", "edges": INTEGRATION_MAP, "modules": list(MODULE_CATALOG)}

    def verify(self) -> dict[str, Any]:
        reg = self.ecosystem.unified_registry()
        names = {m["module"] for m in reg["modules"]}
        missing = [m for m in MODULE_CATALOG if m not in names]
        return {"ok": not missing, "missing": missing, "connected": sorted(names)}

    def status(self) -> dict[str, Any]:
        return {"engineering_integration": "1.0", "map_size": len(INTEGRATION_MAP), "ready": True}


engineering_integration = EngineeringIntegration()
