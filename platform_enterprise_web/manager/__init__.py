"""Web Foundation Manager — Sprint 26.1."""

from __future__ import annotations

from typing import Any

from platform_enterprise_web.models import STACK, WEB_PATH


class WebFoundationManager:
    def plan(self, *, release: str) -> dict[str, Any]:
        if not release:
            raise ValueError("release is required")
        return {
            "release": release,
            "path": WEB_PATH,
            "stack": list(STACK),
            "gate": "enterprise_web_foundation",
            "suites": [
                "shell",
                "auth",
                "layouts",
                "navigation",
                "workspace",
                "theme",
                "ui",
                "i18n",
                "notifications",
                "preferences",
                "dashboard",
            ],
        }
