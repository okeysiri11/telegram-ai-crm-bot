"""Workspace Platform constants — Sprint 26.4."""

from __future__ import annotations

WORKSPACE_PATH = "src/web/workspace"
VERSION = "9.0.5"

ARCHITECTURE = (
    "workspace_manager",
    "dashboard_engine",
    "widget_manager",
    "layout_manager",
    "navigation_hub",
    "quick_actions",
    "favorites_manager",
    "recent_activity",
    "search_center",
    "personalization_engine",
    "workspace_settings",
    "workspace_dashboard",
)

WORKSPACE_KINDS = ("personal", "team", "department", "organization", "project")
DASHBOARD_KINDS = ("personal", "executive", "operations", "finance", "ai", "analytics", "custom")
WIDGET_KINDS = (
    "kpi_cards",
    "charts",
    "ai_assistant",
    "tasks",
    "calendar",
    "notifications",
    "workflow_queue",
    "crm_summary",
    "erp_summary",
    "finance_summary",
    "hr_summary",
    "analytics",
    "marketplace",
    "system_health",
)
LAYOUT_FEATURES = ("drag_drop", "resize", "docking", "responsive_grid", "multi_monitor_ready")
QUICK_ACTIONS = (
    "create_task",
    "create_workflow",
    "open_ai_assistant",
    "start_chat",
    "new_crm_record",
    "upload_document",
    "launch_automation",
)
SEARCH_CATEGORIES = (
    "modules",
    "users",
    "organizations",
    "documents",
    "workflows",
    "ai_agents",
    "reports",
    "tasks",
)
REALTIME_SOURCES = ("websocket", "event_bus", "notification_center", "live_dashboard_refresh")

INTEGRATION_TARGETS = (
    "enterprise_hub",
    "authentication_ui",
    "design_system",
    "ai_orchestrator",
    "workflow_engine",
    "crm_platform",
    "erp_platform",
    "analytics_platform",
    "marketplace",
    "notification_center",
)

KPI_TARGETS = {
    "workspace_ready": True,
    "configurable_dashboards": True,
    "widget_library_ready": True,
    "drag_drop_layout": True,
    "global_search": True,
    "quick_actions": True,
    "personalization": True,
    "realtime_updates": True,
}

PRINCIPLES = (
    "post_login_workspace_home",
    "personalized_dashboards",
    "design_system_widgets",
    "realtime_first",
    "enterprise_service_hub",
    "phase3_workspace_framework",
)
