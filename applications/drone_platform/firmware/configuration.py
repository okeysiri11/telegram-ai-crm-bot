from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError
from applications.drone_platform.shared.store import DroneStore, drone_store


class FirmwareConfigurationManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def save_config(
        self,
        *,
        name: str,
        parameters: dict[str, Any],
        firmware_project_id: str = "",
        profile: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cid = f"cfg_{uuid.uuid4().hex[:12]}"
        record = {
            "config_id": cid,
            "name": name,
            "profile": profile,
            "firmware_project_id": firmware_project_id,
            "parameters": dict(parameters),
            "metadata": dict(metadata or {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.firmware_configs.save(cid, record)
        return record

    def get(self, config_id: str) -> dict[str, Any]:
        item = self.store.firmware_configs.get(config_id)
        if item is None:
            raise NotFoundError("firmware_config", config_id)
        return item

    def list(self) -> list[dict[str, Any]]:
        return self.store.firmware_configs.list_all()

    def preset(self, vehicle: str, use_case: str = "default") -> dict[str, Any]:
        presets = {
            ("copter", "default"): {"FRAME_TYPE": 1, "ATC_RAT_PIT_P": 0.135, "BATT_CAPACITY": 5000},
            ("plane", "default"): {"ARSPD_ENABLE": 1, "TRIM_ARSPD_CM": 1500, "BATT_CAPACITY": 8000},
            ("rover", "default"): {"CRUISE_SPEED": 2.0, "SPEED_TURN_GAIN": 2.0},
        }
        params = presets.get((vehicle.lower(), use_case), {"NOTES": f"preset:{vehicle}:{use_case}"})
        return self.save_config(name=f"{vehicle}-{use_case}", parameters=params, profile=use_case)


firmware_configuration_manager = FirmwareConfigurationManager()
