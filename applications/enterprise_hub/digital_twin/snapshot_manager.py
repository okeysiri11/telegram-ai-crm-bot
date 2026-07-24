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



from applications.enterprise_hub.digital_twin.models import SNAPSHOT_KINDS


class SnapshotManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def capture(self, *, kind: str = "manual", label: str = "", actor: str = "system") -> dict[str, Any]:
        if kind not in SNAPSHOT_KINDS:
            raise ValidationError(f"invalid snapshot kind: {kind}")
        twins = self.store.edt_twins.list_all()
        rels = self.store.edt_relationships.list_all()
        sid = _id("edt_snap")
        return self.store.edt_snapshots.save(
            sid,
            {
                "snapshot_id": sid,
                "kind": kind,
                "label": label or f"{kind}-{_now()}",
                "actor": actor,
                "twin_count": len(twins),
                "relationship_count": len(rels),
                "payload": {
                    "twins": [{k: t.get(k) for k in ("twin_id", "name", "twin_type", "status", "state", "version")} for t in twins],
                    "relationships": rels,
                },
                "captured_at": _now(),
            },
        )

    def restore(self, *, snapshot_id: str) -> dict[str, Any]:
        snap = self.store.edt_snapshots.get(snapshot_id)
        if not snap:
            raise NotFoundError(f"snapshot not found: {snapshot_id}")
        restored = 0
        for t in snap.get("payload", {}).get("twins") or []:
            existing = self.store.edt_twins.get(t["twin_id"])
            if existing:
                existing["state"] = t.get("state")
                existing["status"] = t.get("status", "restored")
                existing["version"] = t.get("version", existing.get("version"))
                existing["updated_at"] = _now()
                self.store.edt_twins.save(t["twin_id"], existing)
                restored += 1
        rid = _id("edt_srest")
        return self.store.edt_snapshot_restores.save(
            rid,
            {"restore_id": rid, "snapshot_id": snapshot_id, "restored": restored, "at": _now()},
        )

    def compare(self, *, snapshot_a: str, snapshot_b: str) -> dict[str, Any]:
        a = self.store.edt_snapshots.get(snapshot_a)
        b = self.store.edt_snapshots.get(snapshot_b)
        if not a or not b:
            raise NotFoundError("snapshot not found")
        map_a = {t["twin_id"]: t for t in a.get("payload", {}).get("twins") or []}
        map_b = {t["twin_id"]: t for t in b.get("payload", {}).get("twins") or []}
        only_a = sorted(set(map_a) - set(map_b))
        only_b = sorted(set(map_b) - set(map_a))
        changed = [tid for tid in set(map_a) & set(map_b) if map_a[tid].get("version") != map_b[tid].get("version")]
        return {
            "snapshot_a": snapshot_a,
            "snapshot_b": snapshot_b,
            "only_in_a": only_a,
            "only_in_b": only_b,
            "changed": changed,
            "delta": len(only_a) + len(only_b) + len(changed),
        }

    def export(self, *, snapshot_id: str) -> dict[str, Any]:
        snap = self.store.edt_snapshots.get(snapshot_id)
        if not snap:
            raise NotFoundError(f"snapshot not found: {snapshot_id}")
        return {"snapshot_id": snapshot_id, "export": snap.get("payload"), "label": snap.get("label"), "kind": snap.get("kind")}

    def status(self) -> dict[str, Any]:
        return {
            "snapshots": len(self.store.edt_snapshots.list_all()),
            "restores": len(self.store.edt_snapshot_restores.list_all()),
        }
