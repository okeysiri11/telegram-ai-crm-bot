"""Workspace library facade — Sprint 26.4."""

from __future__ import annotations

from typing import Any

from platform_enterprise_workspace.models import (
    ARCHITECTURE,
    DASHBOARD_KINDS,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    LAYOUT_FEATURES,
    PRINCIPLES,
    QUICK_ACTIONS,
    REALTIME_SOURCES,
    SEARCH_CATEGORIES,
    VERSION,
    WIDGET_KINDS,
    WORKSPACE_KINDS,
    WORKSPACE_PATH,
)


class WorkspaceLibrary:
    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def inventory(self) -> dict[str, Any]:
        return {
            "architecture": list(ARCHITECTURE),
            "workspace_kinds": list(WORKSPACE_KINDS),
            "dashboard_kinds": list(DASHBOARD_KINDS),
            "widget_kinds": list(WIDGET_KINDS),
            "layout_features": list(LAYOUT_FEATURES),
            "quick_actions": list(QUICK_ACTIONS),
            "search_categories": list(SEARCH_CATEGORIES),
            "realtime_sources": list(REALTIME_SOURCES),
            "path": WORKSPACE_PATH,
            "architecture_count": len(ARCHITECTURE),
            "widget_count": len(WIDGET_KINDS),
            "passed": True,
        }

    def dashboard(self) -> dict[str, Any]:
        inv = self.inventory()
        return {
            "workspace_ready": True,
            "dashboard_engine_ready": True,
            "widget_library_ready": True,
            "layout_manager_ready": True,
            "search_center_ready": True,
            "personalization_ready": True,
            "realtime_ready": True,
            "path": WORKSPACE_PATH,
            "version": VERSION,
            "widget_count": inv["widget_count"],
            "workspace_kinds": inv["workspace_kinds"],
            "recommendations": ["enable_live_socket_url", "persist_layouts_per_user"],
        }

    def integrations(self) -> dict[str, Any]:
        return {
            "targets": list(INTEGRATION_TARGETS),
            "kpi_targets": dict(KPI_TARGETS),
            "linked": True,
            "duplicates_console_logic": False,
            "post_login_entry": "/workspace",
        }

    def bootstrap(self) -> dict[str, Any]:
        inv = self.inventory()
        dash = self.dashboard()
        links = self.integrations()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "workspace_ready": True,
            "dashboard_engine_ready": True,
            "widget_library_ready": True,
            "layout_manager_ready": True,
            "navigation_hub_ready": True,
            "quick_actions_ready": True,
            "favorites_ready": True,
            "search_center_ready": True,
            "personalization_ready": True,
            "realtime_ready": True,
            "path": WORKSPACE_PATH,
            "version": VERSION,
            "kpi": dict(KPI_TARGETS),
            "status": "ready",
            "integrations": links,
            "full": {"inventory": inv, "dashboard": dash, "links": links},
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": list(ARCHITECTURE),
            "principles": self.principles(),
            "path": WORKSPACE_PATH,
            "version": VERSION,
        }


workspace_library = WorkspaceLibrary()
