"""Ground Control Station bridges (Sprint 11.3)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


SUPPORTED_GCS = ("mission_planner", "qgroundcontrol", "mavproxy", "apm_planner", "custom")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GCSBridgeService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def supported(self) -> list[str]:
        return list(SUPPORTED_GCS)

    def create_bridge(
        self,
        *,
        name: str,
        gcs_type: str,
        endpoint: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        gcs_type = gcs_type.lower().strip()
        if gcs_type not in SUPPORTED_GCS:
            raise ValidationError(f"Unsupported GCS type: {gcs_type}")
        bid = f"gcs_{uuid.uuid4().hex[:12]}"
        bridge = {
            "bridge_id": bid,
            "name": name,
            "gcs_type": gcs_type,
            "endpoint": endpoint,
            "status": "configured",
            "metadata": dict(metadata or {}),
            "created_at": _now(),
        }
        self.store.gcs_bridges.save(bid, bridge)
        return bridge

    def connect(self, bridge_id: str) -> dict[str, Any]:
        bridge = self.get(bridge_id)
        bridge["status"] = "connected"
        bridge["connected_at"] = _now()
        self.store.gcs_bridges.save(bridge_id, bridge)
        return bridge

    def sync_mission(self, bridge_id: str, mission: dict[str, Any]) -> dict[str, Any]:
        bridge = self.get(bridge_id)
        return {
            "bridge_id": bridge_id,
            "gcs_type": bridge["gcs_type"],
            "action": "mission_sync",
            "mission_name": mission.get("name", ""),
            "waypoint_count": len(mission.get("waypoints") or []),
            "status": "queued",
            "at": _now(),
        }

    def sync_parameters(self, bridge_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        bridge = self.get(bridge_id)
        return {
            "bridge_id": bridge_id,
            "gcs_type": bridge["gcs_type"],
            "action": "parameter_sync",
            "parameter_count": len(parameters),
            "status": "queued",
            "at": _now(),
        }

    def get(self, bridge_id: str) -> dict[str, Any]:
        item = self.store.gcs_bridges.get(bridge_id)
        if item is None:
            raise NotFoundError("gcs_bridge", bridge_id)
        return item

    def list(self) -> list[dict[str, Any]]:
        return self.store.gcs_bridges.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "gcs_integration": "1.0",
            "supported": self.supported(),
            "bridge_count": self.store.gcs_bridges.count(),
        }


gcs_bridge_service = GCSBridgeService()
