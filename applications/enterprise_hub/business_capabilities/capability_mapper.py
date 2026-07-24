
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

from applications.enterprise_hub.business_capabilities.capability_registry import CapabilityRegistry


class CapabilityMapper:
    """Builds hierarchy maps from parent_key relationships."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = CapabilityRegistry(self.store)

    def hierarchy(self, root_key: str = "enterprise") -> dict[str, Any]:
        items = self.registry.list_all()
        if not items:
            raise ValidationError("no capabilities registered")
        by_key = {i["key"]: i for i in items}
        children: dict[str | None, list[str]] = {}
        for item in items:
            children.setdefault(item.get("parent_key"), []).append(item["key"])

        def build(key: str) -> dict[str, Any]:
            node = by_key.get(key)
            if not node:
                return {"key": key, "missing": True, "children": []}
            return {
                "key": key,
                "name": node["name"],
                "maturity_level": node["maturity_level"],
                "domain": node["domain"],
                "children": [build(c) for c in children.get(key, [])],
            }

        root = build(root_key) if root_key in by_key else {
            "key": root_key,
            "children": [build(k) for k in children.get(None, [])],
        }
        map_id = _id("ebc_map")
        record = {
            "map_id": map_id,
            "root_key": root_key,
            "tree": root,
            "node_count": len(items),
            "mapped_at": _now(),
        }
        self.store.ebc_maps.save(map_id, record)
        return record

    def status(self) -> dict[str, Any]:
        return {"maps": len(self.store.ebc_maps.list_all())}
