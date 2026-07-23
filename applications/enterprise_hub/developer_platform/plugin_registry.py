
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

from applications.enterprise_hub.developer_platform.models import PLUGIN_KINDS, PLUGIN_STATUSES


class PluginRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        plugin_id: str,
        name: str,
        version: str = "1.0.0",
        kind: str = "plugin",
        author: str = "bidex",
        manifest_id: str | None = None,
        permissions: list[str] | None = None,
    ) -> dict[str, Any]:
        if not plugin_id or not name:
            raise ValidationError("plugin_id and name are required")
        if kind not in PLUGIN_KINDS:
            raise ValidationError(f"invalid kind: {kind}")
        existing = self.store.sdp_plugins.get(plugin_id)
        if existing and existing.get("status") in ("active", "loaded", "installed"):
            raise ValidationError(f"plugin already registered: {plugin_id}")
        record = {
            "plugin_id": plugin_id,
            "name": name,
            "version": version,
            "kind": kind,
            "author": author,
            "manifest_id": manifest_id,
            "permissions": list(permissions or []),
            "status": "registered",
            "registered_at": _now(),
            "updated_at": _now(),
        }
        return self.store.sdp_plugins.save(plugin_id, record)

    def get(self, plugin_id: str) -> dict[str, Any]:
        item = self.store.sdp_plugins.get(plugin_id)
        if not item:
            raise NotFoundError(f"plugin not found: {plugin_id}")
        return item

    def set_status(self, plugin_id: str, status: str) -> dict[str, Any]:
        if status not in PLUGIN_STATUSES:
            raise ValidationError(f"invalid status: {status}")
        item = self.get(plugin_id)
        item["status"] = status
        item["updated_at"] = _now()
        return self.store.sdp_plugins.save(plugin_id, item)

    def list_all(self) -> list[dict[str, Any]]:
        return self.store.sdp_plugins.list_all()

    def status(self) -> dict[str, Any]:
        items = self.list_all()
        by_status: dict[str, int] = {}
        for i in items:
            s = i.get("status", "unknown")
            by_status[s] = by_status.get(s, 0) + 1
        return {"plugins": len(items), "by_status": by_status}
