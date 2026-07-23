
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


class PluginLoader:
    """Load plugin packages into the runtime (simulated)."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def load(self, *, plugin_id: str, entrypoint: str = "main:Plugin", hot: bool = False) -> dict[str, Any]:
        plugin = self.store.sdp_plugins.get(plugin_id)
        if not plugin:
            raise NotFoundError(f"plugin not found: {plugin_id}")
        lid = _id("sdp_load")
        record = {
            "load_id": lid,
            "plugin_id": plugin_id,
            "entrypoint": entrypoint,
            "hot": hot,
            "module_path": f"plugins.{plugin_id.replace('-', '_')}",
            "loaded_at": _now(),
            "ok": True,
        }
        self.store.sdp_loads.save(lid, record)
        plugin["status"] = "loaded"
        plugin["load_id"] = lid
        plugin["updated_at"] = _now()
        self.store.sdp_plugins.save(plugin_id, plugin)
        return record

    def unload(self, *, plugin_id: str) -> dict[str, Any]:
        plugin = self.store.sdp_plugins.get(plugin_id)
        if not plugin:
            raise NotFoundError(f"plugin not found: {plugin_id}")
        uid = _id("sdp_unl")
        record = {"unload_id": uid, "plugin_id": plugin_id, "at": _now()}
        plugin["status"] = "installed"
        plugin["updated_at"] = _now()
        self.store.sdp_plugins.save(plugin_id, plugin)
        return record

    def status(self) -> dict[str, Any]:
        return {"loads": len(self.store.sdp_loads.list_all())}
