
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


class PluginValidator:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def validate_manifest(self, manifest: dict[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        if not manifest.get("plugin_id"):
            errors.append("missing plugin_id")
        if not manifest.get("name"):
            errors.append("missing name")
        if not manifest.get("version"):
            errors.append("missing version")
        kind = manifest.get("kind", "plugin")
        if kind not in PLUGIN_KINDS:
            errors.append(f"invalid kind: {kind}")
        for p in manifest.get("permissions") or []:
            if p not in PERMISSIONS:
                errors.append(f"invalid permission: {p}")
        vid = _id("sdp_val")
        result = {
            "validation_id": vid,
            "plugin_id": manifest.get("plugin_id"),
            "valid": not errors,
            "errors": errors,
            "at": _now(),
        }
        return self.store.sdp_validations.save(vid, result)

    def status(self) -> dict[str, Any]:
        items = self.store.sdp_validations.list_all()
        return {"validations": len(items), "passed": sum(1 for i in items if i.get("valid"))}
