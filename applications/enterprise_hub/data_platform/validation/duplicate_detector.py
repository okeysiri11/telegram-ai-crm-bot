"""Duplicate detection for master data."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DuplicateDetector:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def detect(self, *, entity_type: str = "") -> dict[str, Any]:
        items = [
            i
            for i in self.store.edp_entities.list_all()
            if isinstance(i, dict)
            and (not entity_type or i.get("entity_type") == entity_type.lower())
        ]
        by_name: dict[str, list[str]] = {}
        for item in items:
            key = f"{item.get('entity_type')}:{str(item.get('name', '')).strip().lower()}"
            by_name.setdefault(key, []).append(item["entity_id"])
        duplicates = {k: v for k, v in by_name.items() if len(v) > 1}
        did = _id("edp_dup")
        return self.store.edp_duplicates.save(
            did,
            {
                "detection_id": did,
                "entity_type": entity_type.lower(),
                "duplicate_groups": duplicates,
                "count": len(duplicates),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"detections": self.store.edp_duplicates.count()}
