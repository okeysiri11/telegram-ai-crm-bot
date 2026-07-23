"""Marketplace packages catalog."""

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


class PackageCatalog:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def publish(
        self,
        *,
        name: str,
        kind: str = "tool",
        version: str = "1.0.0",
        payload: dict[str, Any] | None = None,
        compatible_with: str = "5.4.2",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name is required")
        if kind not in ("tool", "skill"):
            raise ValidationError("kind must be tool or skill")
        pid = _id("ats_pkg")
        return self.store.ats_packages.save(
            pid,
            {
                "package_id": pid,
                "name": name.strip(),
                "kind": kind,
                "version": version,
                "payload": payload or {},
                "compatible_with": compatible_with,
                "status": "published",
                "at": _now(),
            },
        )

    def get(self, package_id: str) -> dict[str, Any]:
        item = self.store.ats_packages.get(package_id)
        if not item:
            raise NotFoundError(f"package not found: {package_id}")
        return item
