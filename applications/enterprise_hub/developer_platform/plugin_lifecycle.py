
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


class PluginLifecycle:
    """Activate, disable, hot-reload, and rollback plugins."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def activate(self, *, plugin_id: str) -> dict[str, Any]:
        plugin = self._get(plugin_id)
        plugin["status"] = "active"
        plugin["activated_at"] = _now()
        plugin["updated_at"] = _now()
        self.store.sdp_plugins.save(plugin_id, plugin)
        return self._audit(plugin_id, "activate")

    def disable(self, *, plugin_id: str) -> dict[str, Any]:
        plugin = self._get(plugin_id)
        plugin["status"] = "disabled"
        plugin["disabled_at"] = _now()
        plugin["updated_at"] = _now()
        self.store.sdp_plugins.save(plugin_id, plugin)
        return self._audit(plugin_id, "disable")

    def hot_reload(self, *, plugin_id: str) -> dict[str, Any]:
        plugin = self._get(plugin_id)
        hid = _id("sdp_hot")
        record = {
            "reload_id": hid,
            "plugin_id": plugin_id,
            "previous_version": plugin.get("version"),
            "at": _now(),
            "zero_downtime": True,
        }
        plugin["status"] = "active"
        plugin["last_reload_id"] = hid
        plugin["updated_at"] = _now()
        self.store.sdp_plugins.save(plugin_id, plugin)
        self.store.sdp_reloads.save(hid, record)
        self._audit(plugin_id, "hot_reload", extra={"reload_id": hid})
        return record

    def rollback(self, *, plugin_id: str, to_version: str) -> dict[str, Any]:
        plugin = self._get(plugin_id)
        if not to_version:
            raise ValidationError("to_version is required")
        rid = _id("sdp_rb")
        record = {
            "rollback_id": rid,
            "plugin_id": plugin_id,
            "from_version": plugin.get("version"),
            "to_version": to_version,
            "at": _now(),
        }
        plugin["version"] = to_version
        plugin["status"] = "rolled_back"
        plugin["updated_at"] = _now()
        self.store.sdp_plugins.save(plugin_id, plugin)
        self.store.sdp_rollbacks.save(rid, record)
        self._audit(plugin_id, "rollback", extra=record)
        return record

    def _get(self, plugin_id: str) -> dict[str, Any]:
        plugin = self.store.sdp_plugins.get(plugin_id)
        if not plugin:
            raise NotFoundError(f"plugin not found: {plugin_id}")
        return plugin

    def _audit(self, plugin_id: str, action: str, extra: dict | None = None) -> dict[str, Any]:
        aid = _id("sdp_aud")
        record = {
            "audit_id": aid,
            "plugin_id": plugin_id,
            "action": action,
            "at": _now(),
            **(extra or {}),
        }
        return self.store.sdp_audit.save(aid, record)

    def status(self) -> dict[str, Any]:
        return {
            "reloads": len(self.store.sdp_reloads.list_all()),
            "rollbacks": len(self.store.sdp_rollbacks.list_all()),
            "audit_events": len(self.store.sdp_audit.list_all()),
        }
