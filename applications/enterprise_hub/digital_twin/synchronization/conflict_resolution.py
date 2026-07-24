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




class ConflictResolution:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def resolve(
        self,
        *,
        twin_id: str,
        local_state: dict[str, Any],
        remote_state: dict[str, Any],
        strategy: str = "remote_wins",
    ) -> dict[str, Any]:
        twin = self.store.edt_twins.get(twin_id)
        if not twin:
            raise NotFoundError(f"twin not found: {twin_id}")
        if strategy == "local_wins":
            merged = {**remote_state, **local_state}
            winner = "local"
        elif strategy == "merge":
            merged = {**local_state, **remote_state}
            winner = "merge"
        else:
            merged = {**local_state, **remote_state}
            winner = "remote"
        cid = _id("edt_conf")
        return self.store.edt_conflicts.save(
            cid,
            {
                "conflict_id": cid,
                "twin_id": twin_id,
                "strategy": strategy,
                "winner": winner,
                "merged": merged,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"conflicts": len(self.store.edt_conflicts.list_all())}
