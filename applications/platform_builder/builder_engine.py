"""Reusable Builder Engine — identical structure for every builder."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.catalog import BUILDERS, FRAMEWORK_PHASES, get_builder
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


HELP_TONES = {
    "purpose": "What this setting is for",
    "benefits": "How it helps your organization",
    "typical_use": "Where teams usually apply it",
    "business_value": "Business outcomes it supports",
}


class BuilderEngine:
    """Every Builder inherits: Step → Explanation → Information → Example → Preview → Create."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def list_builders(self) -> dict[str, Any]:
        return {
            "framework_phases": list(FRAMEWORK_PHASES),
            "count": len(BUILDERS),
            "items": list(BUILDERS),
        }

    def describe(self, builder_id: str) -> dict[str, Any]:
        builder = get_builder(builder_id)
        if not builder:
            raise NotFoundError(f"Builder not found: {builder_id}")
        steps = builder.get("steps") or []
        return {
            "builder": builder,
            "framework": {
                "phases": list(FRAMEWORK_PHASES),
                "inherited": True,
                "flow": " → ".join(FRAMEWORK_PHASES),
            },
            "steps": [
                {
                    "index": i + 1,
                    "title": title,
                    "phase": FRAMEWORK_PHASES[min(i, len(FRAMEWORK_PHASES) - 1)],
                    "help": self.help_for(builder_id, title),
                }
                for i, title in enumerate(steps)
            ],
            "learning_supported": builder.get("learning_supported", True),
            "frame_only": builder.get("frame_only", True),
        }

    def help_for(self, builder_id: str, item: str) -> dict[str, Any]:
        builder = get_builder(builder_id)
        name = builder["name"] if builder else builder_id
        return {
            "item": item,
            "short_description": f"{item} for {name}",
            "detailed_explanation": (
                f"{item} guides you through a clear configuration step inside {name}. "
                f"Each choice shapes how the resulting object behaves across the platform."
            ),
            "example": f"Example: configure «{item}» to match your team’s operating rhythm.",
            "popup": {
                "title": item,
                "body": f"Use {item} to capture the essentials for {name}.",
            },
            "tooltip": f"Learn about {item}",
            "purpose": HELP_TONES["purpose"],
            "benefits": HELP_TONES["benefits"],
            "typical_use": HELP_TONES["typical_use"],
            "business_value": HELP_TONES["business_value"],
            "tone": "positive_guidance",
        }

    def preview(self, builder_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        builder = get_builder(builder_id)
        if not builder:
            raise NotFoundError(f"Builder not found: {builder_id}")
        if builder.get("kind") not in ("builder",):
            raise ValidationError("Preview is available for builders only")
        rid = _id("prev")
        record = {
            "preview_id": rid,
            "builder_id": builder_id,
            "builder_name": builder["name"],
            "frame_only": True,
            "payload": payload or {},
            "summary": f"Preview ready for {builder['name']} (navigation frame)",
            "created_at": _now(),
        }
        self.store.previews.save(rid, record)
        return record

    def create(self, builder_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        builder = get_builder(builder_id)
        if not builder:
            raise NotFoundError(f"Builder not found: {builder_id}")
        if builder.get("kind") not in ("builder",):
            raise ValidationError("Create is available for builders only")
        rid = _id("create")
        record = {
            "creation_id": rid,
            "builder_id": builder_id,
            "builder_name": builder["name"],
            "frame_only": True,
            "status": "draft_frame",
            "payload": payload or {},
            "message": f"{builder['name']} draft recorded — business logic arrives in a later sprint",
            "created_at": _now(),
        }
        if builder_id == "concierge":
            record["constraint"] = "one_concierge_per_organization"
        self.store.creations.save(rid, record)
        return record
