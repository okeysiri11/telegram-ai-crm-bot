"""Live Preview Engine — Sprint 28.5."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.framework.catalogs import PREVIEW_CAPABILITIES
from applications.platform_builder.framework.validation import ValidationFramework


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LivePreviewEngine:
    """Instant preview, live update, realtime validation, visual summary."""

    def __init__(self) -> None:
        self.validation = ValidationFramework()

    def preview(self, draft: dict[str, Any], *, existing_names: list[str] | None = None) -> dict[str, Any]:
        validation = self.validation.validate(draft=draft, existing_names=existing_names)
        return {
            "instant_preview": True,
            "live_update": True,
            "realtime_validation": validation,
            "visual_summary": {
                "title": draft.get("name") or "Untitled Builder",
                "builder_type": draft.get("builder_type") or "custom",
                "version": draft.get("version") or "1.0.0",
                "components": draft.get("components") or [],
                "steps": draft.get("steps") or [],
                "validation_rules": draft.get("validation_rules") or [],
                "brand": draft.get("brand_color") or "#1B6CA8",
            },
            "capabilities": list(PREVIEW_CAPABILITIES),
            "updated_at": _now(),
            "ready": True,
        }

    def status(self) -> dict[str, Any]:
        return {"ready": True, "capabilities": list(PREVIEW_CAPABILITIES)}
