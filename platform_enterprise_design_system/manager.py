"""Design System Manager — Sprint 26.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_design_system.models import ARCHITECTURE, DESIGN_PATH


class DesignSystemManager:
    def plan(self, *, release: str) -> dict[str, Any]:
        if not release:
            raise ValueError("release is required")
        return {
            "release": release,
            "path": DESIGN_PATH,
            "architecture": list(ARCHITECTURE),
            "gate": "enterprise_design_system",
        }
