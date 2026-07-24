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



from applications.enterprise_hub.digital_twin.twin_engine import TwinEngine


class RealtimeUpdates:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.engine = TwinEngine(self.store)

    def apply(self, *, twin_id: str, payload: dict[str, Any], source: str = "event_bus") -> dict[str, Any]:
        sync = self.engine.synchronize(twin_id=twin_id, payload=payload, source=source)
        uid = _id("edt_rt")
        return self.store.edt_realtime.save(
            uid,
            {"update_id": uid, "sync_id": sync["sync_id"], "twin_id": twin_id, "source": source, "at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"realtime_updates": len(self.store.edt_realtime.list_all())}
