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




class StateManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def update_state(
        self,
        *,
        twin_id: str,
        state: dict[str, Any],
        actor: str = "system",
        source: str = "manual",
    ) -> dict[str, Any]:
        twin = self.store.edt_twins.get(twin_id)
        if not twin:
            raise NotFoundError(f"twin not found: {twin_id}")
        if not isinstance(state, dict) or not state:
            raise ValidationError("state must be a non-empty dict")
        prev = dict(twin.get("state") or {})
        twin["state"] = {**prev, **state}
        twin["version"] = int(twin.get("version", 1)) + 1
        twin["updated_at"] = _now()
        twin.setdefault("history", []).append(
            {"action": "state_update", "at": _now(), "by": actor, "source": source, "state": state}
        )
        self.store.edt_twins.save(twin_id, twin)
        sid = _id("edt_state")
        return self.store.edt_states.save(
            sid,
            {
                "state_id": sid,
                "twin_id": twin_id,
                "previous": prev,
                "current": twin["state"],
                "actor": actor,
                "source": source,
                "version": twin["version"],
                "at": _now(),
            },
        )

    def get_state(self, twin_id: str) -> dict[str, Any]:
        twin = self.store.edt_twins.get(twin_id)
        if not twin:
            raise NotFoundError(f"twin not found: {twin_id}")
        return {"twin_id": twin_id, "state": twin.get("state"), "version": twin.get("version")}

    def status(self) -> dict[str, Any]:
        return {"state_updates": len(self.store.edt_states.list_all())}
