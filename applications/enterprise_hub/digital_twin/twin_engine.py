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



from applications.enterprise_hub.digital_twin.models import TWIN_STATUSES
from applications.enterprise_hub.digital_twin.state_manager import StateManager
from applications.enterprise_hub.digital_twin.twin_registry import TwinRegistry


class TwinEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = TwinRegistry(self.store)
        self.states = StateManager(self.store)

    def create(self, **kwargs: Any) -> dict[str, Any]:
        return self.registry.register(**kwargs)

    def update(self, *, twin_id: str, state: dict[str, Any], actor: str = "system") -> dict[str, Any]:
        return self.states.update_state(twin_id=twin_id, state=state, actor=actor)

    def archive(self, *, twin_id: str, actor: str = "system") -> dict[str, Any]:
        return self._set_status(twin_id, "archived", actor)

    def delete(self, *, twin_id: str, actor: str = "system") -> dict[str, Any]:
        return self._set_status(twin_id, "deleted", actor)

    def restore(self, *, twin_id: str, actor: str = "system") -> dict[str, Any]:
        twin = self.registry.get(twin_id)
        if twin.get("status") not in ("archived", "deleted"):
            raise ValidationError("only archived/deleted twins can be restored")
        return self._set_status(twin_id, "restored", actor)

    def synchronize(self, *, twin_id: str, payload: dict[str, Any], source: str = "event_bus") -> dict[str, Any]:
        twin = self.registry.get(twin_id)
        twin["status"] = "syncing"
        self.store.edt_twins.save(twin_id, twin)
        upd = self.states.update_state(twin_id=twin_id, state=payload, actor="sync", source=source)
        twin = self.registry.get(twin_id)
        twin["status"] = "active"
        twin["updated_at"] = _now()
        self.store.edt_twins.save(twin_id, twin)
        sid = _id("edt_sync")
        return self.store.edt_syncs.save(
            sid,
            {"sync_id": sid, "twin_id": twin_id, "source": source, "state_id": upd["state_id"], "at": _now()},
        )

    def _set_status(self, twin_id: str, status: str, actor: str) -> dict[str, Any]:
        if status not in TWIN_STATUSES:
            raise ValidationError(f"invalid status: {status}")
        twin = self.registry.get(twin_id)
        twin["status"] = status
        twin["updated_at"] = _now()
        twin.setdefault("history", []).append({"action": status, "at": _now(), "by": actor})
        self.store.edt_twins.save(twin_id, twin)
        return twin

    def status(self) -> dict[str, Any]:
        return {
            "registry": self.registry.status(),
            "states": self.states.status(),
            "syncs": len(self.store.edt_syncs.list_all()),
        }
