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



from applications.enterprise_hub.digital_twin.models import ACCESS_LEVELS, TWIN_STATUSES, TWIN_TYPES


class TwinRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        name: str,
        twin_type: str,
        owner: str = "system",
        state: dict[str, Any] | None = None,
        access: str = "internal",
        relationships: list[str] | None = None,
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name is required")
        if twin_type not in TWIN_TYPES:
            raise ValidationError(f"invalid twin_type: {twin_type}")
        if access not in ACCESS_LEVELS:
            raise ValidationError(f"invalid access: {access}")
        tid = _id("edt_twin")
        record = {
            "twin_id": tid,
            "name": name,
            "twin_type": twin_type,
            "owner": owner,
            "access": access,
            "status": "active",
            "state": dict(state or {"status": "ok"}),
            "relationships": list(relationships or []),
            "history": [{"action": "created", "at": _now(), "by": owner}],
            "version": 1,
            "registered_at": _now(),
            "updated_at": _now(),
        }
        return self.store.edt_twins.save(tid, record)

    def get(self, twin_id: str) -> dict[str, Any]:
        item = self.store.edt_twins.get(twin_id)
        if not item:
            raise NotFoundError(f"twin not found: {twin_id}")
        return item

    def list_all(self, *, twin_type: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        items = self.store.edt_twins.list_all()
        if twin_type:
            items = [i for i in items if i.get("twin_type") == twin_type]
        if status:
            items = [i for i in items if i.get("status") == status]
        return items

    def status(self) -> dict[str, Any]:
        items = self.list_all()
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for i in items:
            t = i.get("twin_type", "?")
            s = i.get("status", "?")
            by_type[t] = by_type.get(t, 0) + 1
            by_status[s] = by_status.get(s, 0) + 1
        return {"twins": len(items), "by_type": by_type, "by_status": by_status, "types": list(TWIN_TYPES)}
