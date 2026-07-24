"""Simulation Registry — catalog of registered simulation assets."""

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


class SimulationRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        name: str,
        kind: str = "scenario",
        ref_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name is required")
        rid = _id("esi_reg")
        return self.store.esi_registry.save(
            rid,
            {
                "registry_id": rid,
                "name": name,
                "kind": kind,
                "ref_id": ref_id,
                "metadata": metadata or {},
                "registered_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        items = self.store.esi_registry.list_all()
        by_kind: dict[str, int] = {}
        for i in items:
            k = i.get("kind", "?")
            by_kind[k] = by_kind.get(k, 0) + 1
        return {"entries": len(items), "by_kind": by_kind}
