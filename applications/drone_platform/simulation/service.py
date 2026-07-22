from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.store import DroneStore, drone_store


class SimulationService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create_run(
        self,
        *,
        name: str,
        firmware_project_id: str = "",
        mission_id: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        sid = f"sim_{uuid.uuid4().hex[:12]}"
        run = {
            "simulation_id": sid,
            "name": name,
            "firmware_project_id": firmware_project_id,
            "mission_id": mission_id,
            "parameters": dict(parameters or {}),
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.simulations.save(sid, run)
        return run

    def list_runs(self) -> list[dict[str, Any]]:
        return self.store.simulations.list_all()


simulation_service = SimulationService()
