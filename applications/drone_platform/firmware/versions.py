from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.firmware.service import FirmwareService, firmware_service
from applications.drone_platform.shared.exceptions import NotFoundError
from applications.drone_platform.shared.store import DroneStore, drone_store


class FirmwareVersionManager:
    def __init__(self, store: DroneStore | None = None, firmware: FirmwareService | None = None) -> None:
        self.store = store or drone_store
        self.firmware = firmware or firmware_service

    def set_version(self, firmware_project_id: str, version: str, notes: str = "") -> dict[str, Any]:
        project = self.firmware.get_project(firmware_project_id)
        previous = project.version
        project.version = version
        history = list(project.metadata.get("version_history") or [])
        history.append({
            "from": previous,
            "to": version,
            "notes": notes,
            "at": datetime.now(timezone.utc).isoformat(),
        })
        project.metadata["version_history"] = history
        self.store.firmware_projects.save(firmware_project_id, project)
        return {"firmware_project_id": firmware_project_id, "version": version, "previous": previous, "history": history}

    def history(self, firmware_project_id: str) -> list[dict[str, Any]]:
        project = self.firmware.get_project(firmware_project_id)
        return list(project.metadata.get("version_history") or [])


firmware_version_manager = FirmwareVersionManager()
