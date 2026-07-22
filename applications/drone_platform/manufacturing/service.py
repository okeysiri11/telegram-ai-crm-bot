from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.store import DroneStore, drone_store


class ManufacturingService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create_build(
        self,
        *,
        project_id: str,
        uav_id: str = "",
        status: str = "planned",
        notes: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        bid = f"mfg_{uuid.uuid4().hex[:12]}"
        build = {
            "build_id": bid,
            "project_id": project_id,
            "uav_id": uav_id,
            "status": status,
            "notes": notes,
            "metadata": dict(metadata or {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.manufacturing_builds.save(bid, build)
        return build

    def list_builds(self) -> list[dict[str, Any]]:
        return self.store.manufacturing_builds.list_all()


manufacturing_service = ManufacturingService()
