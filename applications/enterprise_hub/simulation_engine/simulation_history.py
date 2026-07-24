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




class SimulationHistory:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def record(self, *, kind: str, ref_id: str, summary: dict[str, Any] | None = None) -> dict[str, Any]:
        hid = _id("esi_hist")
        return self.store.esi_history.save(
            hid,
            {
                "history_id": hid,
                "kind": kind,
                "ref_id": ref_id,
                "summary": summary or {},
                "at": _now(),
            },
        )

    def list_all(self, *, kind: str | None = None) -> list[dict[str, Any]]:
        items = self.store.esi_history.list_all()
        if kind:
            items = [i for i in items if i.get("kind") == kind]
        return sorted(items, key=lambda x: x.get("at") or "")

    def status(self) -> dict[str, Any]:
        return {"history_events": len(self.store.esi_history.list_all())}
