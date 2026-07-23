
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

from applications.enterprise_hub.developer_platform.models import PERMISSIONS, PLUGIN_KINDS


class ManifestLoader:
    """Load and normalize plugin package manifests."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def load(
        self,
        *,
        plugin_id: str,
        name: str,
        version: str = "1.0.0",
        author: str = "bidex",
        description: str = "",
        kind: str = "plugin",
        dependencies: list[str] | None = None,
        permissions: list[str] | None = None,
        compatibility: str = "5.4.6-enterprise",
        entrypoint: str = "main:Plugin",
    ) -> dict[str, Any]:
        if not plugin_id or not name:
            raise ValidationError("plugin_id and name are required")
        if kind not in PLUGIN_KINDS:
            raise ValidationError(f"invalid kind: {kind}")
        perms = list(permissions or [])
        for p in perms:
            if p not in PERMISSIONS:
                raise ValidationError(f"invalid permission: {p}")
        mid = _id("sdp_mf")
        record = {
            "manifest_id": mid,
            "plugin_id": plugin_id,
            "name": name,
            "version": version,
            "author": author,
            "description": description or name,
            "kind": kind,
            "dependencies": list(dependencies or []),
            "permissions": perms,
            "compatibility": compatibility,
            "entrypoint": entrypoint,
            "loaded_at": _now(),
        }
        return self.store.sdp_manifests.save(mid, record)

    def get(self, manifest_id: str) -> dict[str, Any]:
        item = self.store.sdp_manifests.get(manifest_id)
        if not item:
            raise NotFoundError(f"manifest not found: {manifest_id}")
        return item

    def status(self) -> dict[str, Any]:
        items = self.store.sdp_manifests.list_all()
        return {"manifests": len(items), "items": items}
