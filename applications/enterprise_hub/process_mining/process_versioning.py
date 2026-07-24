from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"




class ProcessVersioning:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def snapshot(self, *, process_id: str, label: str = "") -> dict[str, Any]:
        process = self.store.epm_processes.get(process_id)
        if not process:
            raise NotFoundError(f"process not found: {process_id}")
        vid = _id("epm_ver")
        version = int(process.get("version", 1))
        record = {
            "version_id": vid,
            "process_id": process_id,
            "version": version,
            "label": label or f"v{version}",
            "steps": list(process.get("steps") or []),
            "variants": list(process.get("variants") or []),
            "at": _now(),
        }
        self.store.epm_versions.save(vid, record)
        process["version"] = version + 1
        self.store.epm_processes.save(process_id, process)
        return record

    def status(self) -> dict[str, Any]:
        return {"versions": len(self.store.epm_versions.list_all())}
