
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

from applications.enterprise_hub.business_capabilities.models import (
    CAPABILITY_DOMAINS,
    CAPABILITY_STATUSES,
    MATURITY_LEVELS,
)


_LEVEL_LABELS = dict(MATURITY_LEVELS)


class CapabilityRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        key: str,
        name: str,
        domain: str = "custom",
        owner: str = "system",
        description: str = "",
        strategic_goal: str = "",
        maturity_level: int = 1,
        parent_key: str | None = None,
        kpi: list[str] | None = None,
        processes: list[str] | None = None,
        ai_components: list[str] | None = None,
        digital_twin_ref: str | None = None,
        status: str = "active",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not key or not name:
            raise ValidationError("key and name are required")
        if domain not in CAPABILITY_DOMAINS:
            raise ValidationError(f"invalid domain: {domain}")
        if status not in CAPABILITY_STATUSES:
            raise ValidationError(f"invalid status: {status}")
        level = int(maturity_level)
        if level not in _LEVEL_LABELS:
            raise ValidationError(f"invalid maturity_level: {maturity_level}")
        existing = self.find_by_key(key)
        if existing:
            raise ValidationError(f"capability already registered: {key}")
        cid = _id("ebc_cap")
        return self.store.ebc_capabilities.save(
            cid,
            {
                "capability_id": cid,
                "key": key,
                "name": name,
                "domain": domain,
                "owner": owner,
                "description": description or name,
                "strategic_goal": strategic_goal or f"Advance {name}",
                "maturity_level": level,
                "maturity_label": _LEVEL_LABELS[level],
                "parent_key": parent_key,
                "kpi": list(kpi or []),
                "processes": list(processes or []),
                "ai_components": list(ai_components or []),
                "digital_twin_ref": digital_twin_ref or f"twin:{key}",
                "status": status,
                "metadata": metadata or {},
                "registered_at": _now(),
            },
        )

    def find_by_key(self, key: str) -> dict[str, Any] | None:
        for item in self.store.ebc_capabilities.list_all():
            if item.get("key") == key:
                return item
        return None

    def get(self, capability_id: str) -> dict[str, Any]:
        item = self.store.ebc_capabilities.get(capability_id)
        if not item:
            raise NotFoundError(f"capability not found: {capability_id}")
        return item

    def require_key(self, key: str) -> dict[str, Any]:
        item = self.find_by_key(key)
        if not item:
            raise NotFoundError(f"capability key not found: {key}")
        return item

    def list_all(self) -> list[dict[str, Any]]:
        return self.store.ebc_capabilities.list_all()

    def update_maturity(self, capability_id: str, level: int) -> dict[str, Any]:
        item = self.get(capability_id)
        level = int(level)
        if level not in _LEVEL_LABELS:
            raise ValidationError(f"invalid maturity_level: {level}")
        item["maturity_level"] = level
        item["maturity_label"] = _LEVEL_LABELS[level]
        item["updated_at"] = _now()
        return self.store.ebc_capabilities.save(capability_id, item)

    def status(self) -> dict[str, Any]:
        items = self.list_all()
        return {
            "capabilities": len(items),
            "by_domain": {d: sum(1 for i in items if i.get("domain") == d) for d in CAPABILITY_DOMAINS},
            "by_maturity": {lbl: sum(1 for i in items if i.get("maturity_label") == lbl) for _, lbl in MATURITY_LEVELS},
        }
