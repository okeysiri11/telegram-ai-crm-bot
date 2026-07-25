"""Builder Academy — interactive learning modes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.config import DEFAULT_CONFIG
from applications.platform_builder.shared.exceptions import ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


ACADEMY_MODES = {
    "quick_start": {
        "id": "quick_start",
        "name": "Quick Start",
        "description": "Move quickly through essential steps with compact guidance.",
        "explains_every_screen": False,
    },
    "guided_learning": {
        "id": "guided_learning",
        "name": "Guided Learning",
        "description": "Explain every screen with purpose, benefits, and examples.",
        "explains_every_screen": True,
    },
    "expert": {
        "id": "expert",
        "name": "Expert Mode",
        "description": "Minimal chrome for experienced platform builders.",
        "explains_every_screen": False,
    },
}


class BuilderAcademy:
    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self._enabled_by_builder: dict[str, bool] = {}
        self._mode = "guided_learning"

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "modes": list(ACADEMY_MODES.values()),
            "active_mode": self._mode,
            "mode_detail": ACADEMY_MODES[self._mode],
            "supported_modes": list(DEFAULT_CONFIG.academy_modes),
            "per_builder": dict(self._enabled_by_builder),
        }

    def set_mode(self, mode: str) -> dict[str, Any]:
        if mode not in ACADEMY_MODES:
            raise ValidationError(f"Unknown academy mode: {mode}")
        self._mode = mode
        sid = _id("acad")
        record = {
            "session_id": sid,
            "mode": mode,
            "explains_every_screen": ACADEMY_MODES[mode]["explains_every_screen"],
            "created_at": _now(),
        }
        self.store.academy_sessions.save(sid, record)
        return {"ok": True, **record, "modes": list(ACADEMY_MODES.values())}

    def toggle_learning(self, builder_id: str, enabled: bool) -> dict[str, Any]:
        self._enabled_by_builder[builder_id] = bool(enabled)
        return {
            "ok": True,
            "builder_id": builder_id,
            "learning_enabled": bool(enabled),
            "active_mode": self._mode,
        }

    def screen_guide(self, builder_id: str, screen: str) -> dict[str, Any]:
        mode = ACADEMY_MODES[self._mode]
        enabled = self._enabled_by_builder.get(builder_id, True)
        if not enabled or self._mode == "expert":
            return {
                "builder_id": builder_id,
                "screen": screen,
                "guided": False,
                "mode": self._mode,
                "message": "Learning guidance is quiet in this mode.",
            }
        return {
            "builder_id": builder_id,
            "screen": screen,
            "guided": True,
            "mode": self._mode,
            "explains_every_screen": mode["explains_every_screen"],
            "title": f"Learning: {screen}",
            "purpose": f"Understand how «{screen}» contributes to a complete configuration.",
            "benefits": "Clear steps reduce rework and keep teams aligned.",
            "typical_use": "Use while onboarding new builders or designing a first object.",
            "business_value": "Faster time-to-value with consistent builder quality.",
        }
