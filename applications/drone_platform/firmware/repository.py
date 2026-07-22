from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store

SUPPORTED_ARTIFACT_TYPES = (".bin", ".hex", ".apj", ".param", ".waypoints", ".mission", ".dump")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FirmwareRepository:
    """Firmware artifact repository for engineering artifacts."""

    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def add_artifact(
        self,
        *,
        name: str,
        artifact_type: str,
        content: str = "",
        firmware_project_id: str = "",
        version: str = "",
        metadata: dict[str, Any] | None = None,
        artifact_id: str | None = None,
    ) -> dict[str, Any]:
        ext = artifact_type if artifact_type.startswith(".") else f".{artifact_type}"
        if ext not in SUPPORTED_ARTIFACT_TYPES and ext not in {".param.bak", ".backup"}:
            # allow .param backup aliases
            if not any(ext.endswith(s) or s in ext for s in (".bin", ".hex", ".apj", ".param", ".mission", ".waypoints", ".dump", ".bak", ".backup")):
                raise ValidationError(f"Unsupported artifact type: {artifact_type}")
        aid = artifact_id or f"art_{uuid.uuid4().hex[:12]}"
        digest = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()
        record = {
            "artifact_id": aid,
            "name": name,
            "artifact_type": ext,
            "content": content,
            "size_bytes": len(content.encode("utf-8", errors="ignore")),
            "sha256": digest,
            "firmware_project_id": firmware_project_id,
            "version": version,
            "metadata": dict(metadata or {}),
            "created_at": _now(),
        }
        self.store.firmware_artifacts.save(aid, record)
        return record

    def get(self, artifact_id: str) -> dict[str, Any]:
        item = self.store.firmware_artifacts.get(artifact_id)
        if item is None:
            raise NotFoundError("firmware_artifact", artifact_id)
        return item

    def list(self, artifact_type: str | None = None) -> list[dict[str, Any]]:
        items = self.store.firmware_artifacts.list_all()
        if artifact_type:
            ext = artifact_type if artifact_type.startswith(".") else f".{artifact_type}"
            return [a for a in items if a.get("artifact_type") == ext]
        return items


firmware_repository = FirmwareRepository()
