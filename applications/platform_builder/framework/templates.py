"""Template Engine — Sprint 28.5."""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class TemplateEngine:
    """Save builders as templates, clone, duplicate configurations."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def save_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = (payload.get("name") or "").strip()
        builder_type = (payload.get("builder_type") or "").strip()
        if not name:
            raise ValidationError("Template name is required")
        if not builder_type:
            raise ValidationError("builder_type is required")
        tid = _id("btpl")
        record = {
            "template_id": tid,
            "name": name,
            "builder_type": builder_type,
            "config": copy.deepcopy(payload.get("config") or {}),
            "components": list(payload.get("components") or []),
            "validation_rules": list(payload.get("validation_rules") or []),
            "schema": payload.get("schema") or {},
            "created_at": _now(),
            "source": "universal_builder_framework",
            "sprint": "28.5",
        }
        self.store.builder_templates.save(tid, record)
        return record

    def get(self, template_id: str) -> dict[str, Any]:
        item = self.store.builder_templates.get(template_id)
        if not item:
            raise NotFoundError(f"Template not found: {template_id}")
        return item

    def clone(self, template_id: str, *, new_name: str | None = None) -> dict[str, Any]:
        source = self.get(template_id)
        return self.save_template(
            {
                "name": new_name or f"{source['name']} Copy",
                "builder_type": source["builder_type"],
                "config": source.get("config") or {},
                "components": source.get("components") or [],
                "validation_rules": source.get("validation_rules") or [],
                "schema": source.get("schema") or {},
            }
        )

    def duplicate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        return copy.deepcopy(config)

    def list_all(self) -> dict[str, Any]:
        items = self.store.builder_templates.list_all()
        return {"count": len(items), "items": items}

    def status(self) -> dict[str, Any]:
        return {"ready": True, "operational": True, **self.list_all()}
