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



from applications.enterprise_hub.process_mining.models import PROCESS_STATUSES


class ProcessRepository:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def save(
        self,
        *,
        name: str,
        steps: list[str],
        status: str = "discovered",
        variants: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not name or not steps:
            raise ValidationError("name and steps are required")
        if status not in PROCESS_STATUSES:
            raise ValidationError(f"invalid status: {status}")
        pid = _id("epm_proc")
        return self.store.epm_processes.save(
            pid,
            {
                "process_id": pid,
                "name": name,
                "steps": list(steps),
                "status": status,
                "variants": list(variants or []),
                "metadata": metadata or {},
                "version": 1,
                "saved_at": _now(),
            },
        )

    def get(self, process_id: str) -> dict[str, Any]:
        item = self.store.epm_processes.get(process_id)
        if not item:
            raise NotFoundError(f"process not found: {process_id}")
        return item

    def list_all(self) -> list[dict[str, Any]]:
        return self.store.epm_processes.list_all()

    def status(self) -> dict[str, Any]:
        items = self.list_all()
        return {"processes": len(items), "by_status": {s: sum(1 for i in items if i.get("status") == s) for s in PROCESS_STATUSES}}
