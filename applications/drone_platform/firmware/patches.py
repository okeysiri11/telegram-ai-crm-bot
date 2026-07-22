from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError
from applications.drone_platform.shared.store import DroneStore, drone_store


class FirmwarePatchManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create_patch(
        self,
        *,
        firmware_project_id: str,
        title: str,
        diff: str,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        pid = f"pat_{uuid.uuid4().hex[:12]}"
        record = {
            "patch_id": pid,
            "firmware_project_id": firmware_project_id,
            "title": title,
            "description": description,
            "diff": diff,
            "status": "proposed",
            "metadata": dict(metadata or {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.firmware_patches.save(pid, record)
        return record

    def get(self, patch_id: str) -> dict[str, Any]:
        item = self.store.firmware_patches.get(patch_id)
        if item is None:
            raise NotFoundError("firmware_patch", patch_id)
        return item

    def list(self, firmware_project_id: str | None = None) -> list[dict[str, Any]]:
        items = self.store.firmware_patches.list_all()
        if firmware_project_id:
            return [p for p in items if p.get("firmware_project_id") == firmware_project_id]
        return items


firmware_patch_manager = FirmwarePatchManager()
