"""Documentation dashboard — Sprint 21.6."""

from __future__ import annotations

from typing import Any


class DocumentationDashboard:
    def render(
        self,
        *,
        registry_status: dict[str, Any],
        quality: dict[str, Any],
        publish: dict[str, Any],
        version: str,
    ) -> dict[str, Any]:
        return {
            "version": version,
            "total_docs": registry_status.get("docs", 0),
            "by_category": registry_status.get("by_category", {}),
            "quality_passed": quality.get("passed", False),
            "completeness": quality.get("completeness", 0.0),
            "published_formats": len(publish.get("artifacts", [])),
            "developer_portal": publish.get("portals", {}).get("developer", False),
            "administrator_portal": publish.get("portals", {}).get("administrator", False),
            "status": "ready" if quality.get("passed") else "needs_attention",
        }
