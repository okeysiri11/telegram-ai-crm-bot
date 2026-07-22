from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError
from applications.drone_platform.shared.store import DroneStore, drone_store


class FirmwareReleaseManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create_release(
        self,
        *,
        firmware_project_id: str,
        version: str,
        notes: str = "",
        artifact_ids: list[str] | None = None,
        channel: str = "stable",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        rid = f"rel_{uuid.uuid4().hex[:12]}"
        record = {
            "release_id": rid,
            "firmware_project_id": firmware_project_id,
            "version": version,
            "notes": notes,
            "channel": channel,
            "artifact_ids": list(artifact_ids or []),
            "metadata": dict(metadata or {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.firmware_releases.save(rid, record)
        return record

    def get(self, release_id: str) -> dict[str, Any]:
        item = self.store.firmware_releases.get(release_id)
        if item is None:
            raise NotFoundError("firmware_release", release_id)
        return item

    def list(self, firmware_project_id: str | None = None) -> list[dict[str, Any]]:
        items = self.store.firmware_releases.list_all()
        if firmware_project_id:
            return [r for r in items if r.get("firmware_project_id") == firmware_project_id]
        return items

    def summarize_changes(self, release_id: str, previous_release_id: str | None = None) -> dict[str, Any]:
        current = self.get(release_id)
        previous = self.store.firmware_releases.get(previous_release_id) if previous_release_id else None
        return {
            "release": current,
            "previous": previous,
            "summary": current.get("notes") or f"Release {current.get('version')}",
            "artifact_count": len(current.get("artifact_ids") or []),
        }


firmware_release_manager = FirmwareReleaseManager()
