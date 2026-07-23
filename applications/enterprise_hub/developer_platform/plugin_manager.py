
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

from applications.enterprise_hub.developer_platform.manifest import ManifestLoader
from applications.enterprise_hub.developer_platform.plugin_lifecycle import PluginLifecycle
from applications.enterprise_hub.developer_platform.plugin_loader import PluginLoader
from applications.enterprise_hub.developer_platform.plugin_registry import PluginRegistry
from applications.enterprise_hub.developer_platform.validator import PluginValidator


class PluginManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = PluginRegistry(self.store)
        self.loader = PluginLoader(self.store)
        self.lifecycle = PluginLifecycle(self.store)
        self.manifests = ManifestLoader(self.store)
        self.validator = PluginValidator(self.store)

    def install_from_manifest(
        self,
        *,
        plugin_id: str,
        name: str,
        version: str = "1.0.0",
        kind: str = "plugin",
        author: str = "bidex",
        description: str = "",
        dependencies: list[str] | None = None,
        permissions: list[str] | None = None,
        activate: bool = True,
    ) -> dict[str, Any]:
        mf = self.manifests.load(
            plugin_id=plugin_id,
            name=name,
            version=version,
            author=author,
            description=description,
            kind=kind,
            dependencies=dependencies,
            permissions=permissions,
        )
        validation = self.validator.validate_manifest(mf)
        if not validation["valid"]:
            raise ValidationError(f"invalid manifest: {validation['errors']}")
        reg = self.registry.register(
            plugin_id=plugin_id,
            name=name,
            version=version,
            kind=kind,
            author=author,
            manifest_id=mf["manifest_id"],
            permissions=permissions,
        )
        reg["status"] = "installed"
        reg["installed_at"] = _now()
        reg["owner"] = author
        self.store.sdp_plugins.save(plugin_id, reg)
        load = self.loader.load(plugin_id=plugin_id, entrypoint=mf.get("entrypoint", "main:Plugin"))
        result: dict[str, Any] = {
            "plugin_id": plugin_id,
            "manifest_id": mf["manifest_id"],
            "validation_id": validation["validation_id"],
            "load_id": load["load_id"],
            "status": "loaded",
        }
        if activate:
            act = self.lifecycle.activate(plugin_id=plugin_id)
            result["audit_id"] = act["audit_id"]
            result["status"] = "active"
        return result

    def status(self) -> dict[str, Any]:
        return {
            "registry": self.registry.status(),
            "loader": self.loader.status(),
            "lifecycle": self.lifecycle.status(),
            "manifests": self.manifests.status()["manifests"],
        }
