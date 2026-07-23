"""Knowledge synchronization — incremental sync, conflicts, history, audit, monitor."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class KnowledgeSynchronization:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def sync(
        self, *, platform: str, mode: str = "incremental", changes: int = 0
    ) -> dict[str, Any]:
        if not platform:
            raise ValidationError("platform required")
        sid = _id("kg_sync")
        return self.store.kg_syncs.save(
            sid,
            {
                "sync_id": sid,
                "platform": platform.lower(),
                "mode": mode,
                "changes": int(changes),
                "status": "synced",
                "at": _now(),
            },
        )

    def conflict(
        self, *, entity_ref: str, detail: str = "", resolved: bool = False
    ) -> dict[str, Any]:
        if not entity_ref:
            raise ValidationError("entity_ref required")
        cid = _id("kg_conf")
        return self.store.kg_conflicts.save(
            cid,
            {
                "conflict_id": cid,
                "entity_ref": entity_ref,
                "detail": detail or "duplicate or divergent attributes",
                "resolved": bool(resolved),
                "at": _now(),
            },
        )

    def resolve(self, *, conflict_id: str, resolution: str = "keep_latest") -> dict[str, Any]:
        conf = self.store.kg_conflicts.get(conflict_id)
        if conf is None:
            from applications.enterprise_hub.shared.exceptions import NotFoundError

            raise NotFoundError(f"conflict not found: {conflict_id}")
        conf["resolved"] = True
        conf["resolution"] = resolution
        self.store.kg_conflicts.save(conflict_id, conf)
        rid = _id("kg_res")
        return self.store.kg_resolutions.save(
            rid,
            {
                "resolution_id": rid,
                "conflict_id": conflict_id,
                "resolution": resolution,
                "at": _now(),
            },
        )

    def audit(self, *, action: str, actor: str = "system", detail: str = "") -> dict[str, Any]:
        if not action:
            raise ValidationError("action required")
        aid = _id("kg_aud")
        return self.store.kg_audit.save(
            aid,
            {"audit_id": aid, "action": action, "actor": actor, "detail": detail, "at": _now()},
        )

    def monitor(self) -> dict[str, Any]:
        mid = _id("kg_mon")
        snapshot = {
            "syncs": self.store.kg_syncs.count(),
            "conflicts": self.store.kg_conflicts.count(),
            "resolutions": self.store.kg_resolutions.count(),
        }
        return self.store.kg_sync_monitors.save(
            mid, {"monitor_id": mid, "snapshot": snapshot, "at": _now()}
        )

    def status(self) -> dict[str, Any]:
        return {
            "syncs": self.store.kg_syncs.count(),
            "conflicts": self.store.kg_conflicts.count(),
            "resolutions": self.store.kg_resolutions.count(),
            "audit": self.store.kg_audit.count(),
            "monitors": self.store.kg_sync_monitors.count(),
        }
