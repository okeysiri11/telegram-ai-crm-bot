"""Builder Registry — Sprint 28.5."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.framework.catalogs import TARGET_BUILDERS, UI_COMPONENTS, VALIDATION_RULES
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class BuilderTypeRegistry:
    """Registers builder type, version, schema, components, templates, validation rules."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def seed_known_builders(self) -> dict[str, Any]:
        seeded = []
        for item in TARGET_BUILDERS:
            if item["id"] == "future":
                continue
            existing = self.get(item["id"])
            if existing:
                seeded.append(existing)
                continue
            seeded.append(
                self.register(
                    {
                        "builder_type": item["id"],
                        "name": item["name"],
                        "version": "1.0.0",
                        "status": item["status"],
                        "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
                        "components": list(UI_COMPONENTS)[:6],
                        "templates": [],
                        "validation_rules": [r["id"] for r in VALIDATION_RULES[:4]],
                        "source": "seed",
                    }
                )
            )
        return {"count": len(seeded), "items": seeded}

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        builder_type = (payload.get("builder_type") or "").strip()
        if not builder_type:
            raise ValidationError("builder_type is required")
        existing = self.get(builder_type)
        rid = existing["registry_id"] if existing else _id("breg")
        record = {
            "registry_id": rid,
            "builder_type": builder_type,
            "name": payload.get("name") or builder_type.replace("_", " ").title(),
            "version": payload.get("version") or "1.0.0",
            "schema": payload.get("schema") or {},
            "components": list(payload.get("components") or []),
            "templates": list(payload.get("templates") or []),
            "validation_rules": list(payload.get("validation_rules") or []),
            "status": payload.get("status") or "registered",
            "lifecycle": list(payload.get("lifecycle") or []),
            "extensions": list(payload.get("extensions") or []),
            "registered_at": existing["registered_at"] if existing else _now(),
            "updated_at": _now(),
            "source": payload.get("source") or "universal_builder_framework",
            "sprint": "28.5",
            "registry": "platform_builder_builder_registry",
        }
        self.store.builder_type_registry.save(builder_type, record)
        return record

    def get(self, builder_type: str) -> dict[str, Any] | None:
        return self.store.builder_type_registry.get(builder_type)

    def require(self, builder_type: str) -> dict[str, Any]:
        item = self.get(builder_type)
        if not item:
            raise NotFoundError(f"Builder type not found: {builder_type}")
        return item

    def list_all(self) -> dict[str, Any]:
        items = self.store.builder_type_registry.list_all()
        return {
            "count": len(items),
            "items": items,
            "registry": "platform_builder_builder_registry",
        }

    def status(self) -> dict[str, Any]:
        return {"ready": True, "operational": True, **self.list_all()}
