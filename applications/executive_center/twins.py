"""Digital Twin Engine — application/infra/business/knowledge/agent/workflow/drone/marketplace twins (Sprint 12.3)."""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.executive_center.config import DEFAULT_CONFIG
from applications.executive_center.shared.exceptions import NotFoundError, ValidationError
from applications.executive_center.shared.store import ExecutiveCenterStore, executive_center_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DigitalTwinEngine:
    def __init__(self, store: ExecutiveCenterStore | None = None) -> None:
        self.store = store or executive_center_store
        self.twin_types = list(DEFAULT_CONFIG.twin_types)

    def create(
        self,
        *,
        twin_type: str,
        name: str,
        source_id: str = "",
        state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if twin_type not in self.twin_types:
            raise ValidationError(f"twin_type must be one of {self.twin_types}")
        if not name:
            raise ValidationError("name required")
        tid = f"twin_{uuid.uuid4().hex[:12]}"
        twin = {
            "twin_id": tid,
            "twin_type": twin_type,
            "name": name,
            "source_id": source_id,
            "state": dict(state or {"status": "online"}),
            "synced": False,
            "metadata": dict(metadata or {}),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.twins.save(tid, twin)
        self._snapshot(tid, twin["state"], label="create")
        return twin

    def get(self, twin_id: str) -> dict[str, Any]:
        item = self.store.twins.get(twin_id)
        if item is None:
            raise NotFoundError("twin", twin_id)
        return item

    def live_sync(self, twin_id: str, *, state: dict[str, Any]) -> dict[str, Any]:
        twin = self.get(twin_id)
        twin["state"] = {**twin.get("state", {}), **state}
        twin["synced"] = True
        twin["updated_at"] = _now()
        self.store.twins.save(twin_id, twin)
        self._snapshot(twin_id, twin["state"], label="sync")
        return twin

    def sync_all(self) -> dict[str, Any]:
        twins = self.store.twins.list_all()
        for twin in twins:
            twin["synced"] = True
            twin["updated_at"] = _now()
            self.store.twins.save(twin["twin_id"], twin)
            self._snapshot(twin["twin_id"], twin.get("state") or {}, label="sync_all")
        return {"synced": len(twins), "at": _now()}

    def state_history(self, twin_id: str) -> list[dict[str, Any]]:
        self.get(twin_id)
        return [s for s in self.store.twin_snapshots.list_all() if s.get("twin_id") == twin_id]

    def time_travel(self, twin_id: str, *, snapshot_id: str) -> dict[str, Any]:
        twin = self.get(twin_id)
        snap = self.store.twin_snapshots.get(snapshot_id)
        if snap is None or snap.get("twin_id") != twin_id:
            raise NotFoundError("twin_snapshot", snapshot_id)
        twin["state"] = copy.deepcopy(snap.get("state") or {})
        twin["synced"] = False
        twin["time_travel_to"] = snapshot_id
        twin["updated_at"] = _now()
        self.store.twins.save(twin_id, twin)
        return twin

    def list_twins(self, *, twin_type: str | None = None) -> list[dict[str, Any]]:
        items = self.store.twins.list_all()
        if twin_type:
            items = [i for i in items if i.get("twin_type") == twin_type]
        return items

    def ensure_ecosystem_twins(self) -> list[dict[str, Any]]:
        """Create default twins for known ecosystem surfaces without rewriting apps."""
        defaults = [
            ("application", "AI Ecosystem"),
            ("application", "Drone Platform"),
            ("application", "Marketplace"),
            ("application", "Workflow Studio"),
            ("infrastructure", "Primary Cluster"),
            ("business", "Enterprise Ops"),
            ("knowledge", "Global Knowledge Graph"),
            ("agent", "Chief AI"),
            ("workflow", "Executive Automation"),
            ("drone", "Fleet Twin"),
            ("marketplace", "Plugin Store Twin"),
        ]
        existing = {(t.get("twin_type"), t.get("name")) for t in self.list_twins()}
        created = []
        for twin_type, name in defaults:
            if (twin_type, name) in existing:
                continue
            created.append(self.create(twin_type=twin_type, name=name, state={"bootstrap": True}))
        return created

    def _snapshot(self, twin_id: str, state: dict[str, Any], *, label: str) -> dict[str, Any]:
        sid = f"snap_{uuid.uuid4().hex[:12]}"
        row = {"snapshot_id": sid, "twin_id": twin_id, "label": label, "state": copy.deepcopy(state), "at": _now()}
        self.store.twin_snapshots.save(sid, row)
        return row

    def status(self) -> dict[str, Any]:
        return {
            "digital_twin": "1.0",
            "twins": len(self.list_twins()),
            "snapshots": len(self.store.twin_snapshots.list_all()),
            "types": self.twin_types,
            "ready": True,
        }


digital_twin_engine = DigitalTwinEngine()
