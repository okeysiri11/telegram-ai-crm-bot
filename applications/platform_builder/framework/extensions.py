"""Extension System — Sprint 28.5."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.framework.catalogs import EXTENSION_TYPES
from applications.platform_builder.shared.exceptions import ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


ALLOWED_EXTENSION_IDS = (
    "plugins",
    "custom_steps",
    "custom_validation",
    "custom_components",
    "marketplace_extensions",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class ExtensionSystem:
    """Plugins, custom steps, validation, components, future marketplace extensions."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = (payload.get("name") or "").strip()
        if not name:
            raise ValidationError("Extension name is required")
        ext_type = (payload.get("extension_type") or "plugins").strip().lower().replace(" ", "_")
        if ext_type not in ALLOWED_EXTENSION_IDS:
            raise ValidationError(f"Unsupported extension type: {ext_type}")
        eid = _id("bext")
        record = {
            "extension_id": eid,
            "name": name,
            "extension_type": ext_type,
            "builder_type": payload.get("builder_type"),
            "payload": payload.get("payload") or {},
            "marketplace_ready": bool(payload.get("marketplace_ready")),
            "registered_at": _now(),
            "source": "universal_builder_framework",
            "sprint": "28.5",
        }
        self.store.builder_extensions.save(eid, record)
        return record

    def list_all(self) -> dict[str, Any]:
        items = self.store.builder_extensions.list_all()
        return {"count": len(items), "items": items, "supported_types": list(EXTENSION_TYPES)}

    def status(self) -> dict[str, Any]:
        return {"ready": True, "operational": True, **self.list_all()}
