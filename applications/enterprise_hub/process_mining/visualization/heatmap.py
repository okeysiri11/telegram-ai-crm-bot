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



class Heatmap:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def render(self, *, process_id: str) -> dict[str, Any]:
        process = self.store.epm_processes.get(process_id)
        if not process:
            raise NotFoundError(f"process not found: {process_id}")
        heat = {}
        for v in process.get("variants") or []:
            for step in v.get("path") or []:
                heat[step] = heat.get(step, 0) + int(v.get("count", 1))
        hid = _id("epm_heat")
        return self.store.epm_visualizations.save(
            hid,
            {"visualization_id": hid, "kind": "heatmap", "process_id": process_id, "heat": heat, "at": _now()},
        )
