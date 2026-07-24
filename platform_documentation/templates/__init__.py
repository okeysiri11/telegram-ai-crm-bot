"""Documentation templates — Sprint 21.6."""

from __future__ import annotations

from typing import Any

from platform_documentation.models import DOC_CATEGORIES


class TemplateCatalog:
    def list_all(self) -> list[dict[str, Any]]:
        return [
            {
                "template_id": f"tpl_{cat}",
                "category": cat,
                "sections": ["overview", "details", "examples", "references"],
            }
            for cat in DOC_CATEGORIES
        ]

    def render(self, *, category: str, title: str, body: str = "") -> dict[str, Any]:
        tpl = next((t for t in self.list_all() if t["category"] == category), None)
        if not tpl:
            raise ValueError(f"unknown category: {category}")
        return {
            "category": category,
            "title": title,
            "template_id": tpl["template_id"],
            "sections": tpl["sections"],
            "body": body or f"# {title}\n\nAuto-generated {category} documentation.",
        }
