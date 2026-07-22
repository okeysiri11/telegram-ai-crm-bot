"""External integrations for mission operations (Sprint 11.7)."""

from __future__ import annotations

from typing import Any

from applications.drone_platform.gcs.bridge import GCSBridgeService, gcs_bridge_service


INTEGRATIONS = (
    "mission_planner",
    "qgroundcontrol",
    "ardupilot",
    "px4",
    "mavproxy",
    "mavlink_router",
    "ros2",
)


class MissionOpsIntegrations:
    def __init__(self, gcs: GCSBridgeService | None = None) -> None:
        self.gcs = gcs or gcs_bridge_service

    def supported(self) -> list[str]:
        return list(INTEGRATIONS)

    def connect(self, *, system: str, endpoint: str = "") -> dict[str, Any]:
        system = system.lower().strip()
        if system not in INTEGRATIONS:
            return {"system": system, "connected": False, "error": "unsupported"}
        if system in {"mission_planner", "qgroundcontrol", "mavproxy"}:
            bridge = self.gcs.create_bridge(name=f"{system}-ops", gcs_type=system if system != "mavproxy" else "mavproxy", endpoint=endpoint)
            return {"system": system, "connected": True, "bridge": bridge}
        return {
            "system": system,
            "connected": True,
            "endpoint": endpoint,
            "bridge_type": "protocol_adapter",
            "note": f"{system} adapter ready for mission ops",
        }

    def status(self) -> dict[str, Any]:
        return {"mission_ops_integrations": "1.0", "supported": self.supported(), "gcs": self.gcs.status()}


mission_ops_integrations = MissionOpsIntegrations()
