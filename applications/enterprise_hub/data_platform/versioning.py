"""Version control — record versions, compare, rollback, restore."""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DataVersioning:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def snapshot(self, *, entity_id: str, note: str = "") -> dict[str, Any]:
        entity = self.store.edp_entities.get(entity_id)
        if entity is None:
            raise NotFoundError(f"entity not found: {entity_id}")
        entity["version"] = int(entity.get("version", 1)) + 1
        entity["at"] = _now()
        self.store.edp_entities.save(entity_id, entity)
        vid = _id("edp_ver")
        return self.store.edp_versions.save(
            vid,
            {
                "version_id": vid,
                "entity_id": entity_id,
                "version": entity["version"],
                "snapshot": copy.deepcopy(entity),
                "note": note,
                "at": _now(),
            },
        )

    def compare(self, *, version_id_a: str, version_id_b: str) -> dict[str, Any]:
        a = self.store.edp_versions.get(version_id_a)
        b = self.store.edp_versions.get(version_id_b)
        if a is None or b is None:
            raise NotFoundError("version not found")
        cid = _id("edp_cmp")
        return self.store.edp_version_comps.save(
            cid,
            {
                "compare_id": cid,
                "version_id_a": version_id_a,
                "version_id_b": version_id_b,
                "same_entity": a.get("entity_id") == b.get("entity_id"),
                "version_delta": int(b.get("version", 0)) - int(a.get("version", 0)),
                "at": _now(),
            },
        )

    def rollback(self, *, version_id: str) -> dict[str, Any]:
        ver = self.store.edp_versions.get(version_id)
        if ver is None:
            raise NotFoundError(f"version not found: {version_id}")
        snap = ver.get("snapshot")
        if not isinstance(snap, dict):
            raise ValidationError("invalid snapshot")
        entity_id = ver["entity_id"]
        restored = copy.deepcopy(snap)
        restored["at"] = _now()
        self.store.edp_entities.save(entity_id, restored)
        rid = _id("edp_rb")
        return self.store.edp_rollbacks.save(
            rid,
            {
                "rollback_id": rid,
                "version_id": version_id,
                "entity_id": entity_id,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "versions": self.store.edp_versions.count(),
            "compares": self.store.edp_version_comps.count(),
            "rollbacks": self.store.edp_rollbacks.count(),
        }
