"""Design documentation generator — Sprint 26.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_design_system.models import DOC_SECTIONS


class DesignDocumentation:
    def generate(self, *, catalog: dict[str, Any], tokens: dict[str, Any], themes: dict[str, Any], a11y: dict[str, Any], responsive: dict[str, Any]) -> dict[str, Any]:
        return {
            "sections": list(DOC_SECTIONS),
            "component_guide": catalog.get("components", []),
            "ui_guidelines": [
                "Use design tokens only",
                "Prefer composition over one-off styles",
                "One primary action per view",
                "Support keyboard and screen readers by default",
            ],
            "design_tokens_reference": tokens,
            "theme_documentation": themes,
            "accessibility_guide": a11y,
            "responsive_guide": responsive,
            "passed": True,
        }
