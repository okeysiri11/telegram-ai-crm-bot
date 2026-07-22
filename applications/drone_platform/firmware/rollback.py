from __future__ import annotations

from typing import Any

from applications.drone_platform.firmware.service import FirmwareService, firmware_service
from applications.drone_platform.shared.exceptions import NotFoundError
from applications.drone_platform.shared.store import DroneStore, drone_store


class FirmwareRollbackManager:
    def __init__(self, store: DroneStore | None = None, firmware: FirmwareService | None = None) -> None:
        self.store = store or drone_store
        self.firmware = firmware or firmware_service

    def rollback_firmware(self, backup_id: str) -> dict[str, Any]:
        project = self.firmware.restore_firmware(backup_id)
        return {"status": "rolled_back", "project": project.to_dict(), "backup_id": backup_id}

    def rollback_parameters(self, parameter_set_id: str, target_name: str = "rollback") -> dict[str, Any]:
        restored = self.firmware.restore_parameters(parameter_set_id, target_name=target_name)
        return {"status": "parameters_rolled_back", "parameter_set": restored.to_dict()}


firmware_rollback_manager = FirmwareRollbackManager()
