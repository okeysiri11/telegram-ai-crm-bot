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



class ProcessGraph:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def render(self, *, process_id: str) -> dict[str, Any]:
        process = self.store.epm_processes.get(process_id)
        if not process:
            raise NotFoundError(f"process not found: {process_id}")
        steps = process.get("steps") or []
        nodes = [{"id": s, "label": s} for s in steps]
        edges = [{"from": steps[i], "to": steps[i + 1]} for i in range(len(steps) - 1)]
        gid = _id("epm_graph")
        return self.store.epm_visualizations.save(
            gid,
            {"visualization_id": gid, "kind": "process_graph", "process_id": process_id, "nodes": nodes, "edges": edges, "at": _now()},
        )
