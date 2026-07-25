"""Navigation Platform constants — Sprint 26.5."""

from __future__ import annotations

NAV_PATH = "src/web/navigation"
VERSION = "9.0.5"

ARCHITECTURE = (
    "navigation_manager",
    "menu_engine",
    "command_palette",
    "global_search",
    "search_index",
    "search_provider",
    "recent_manager",
    "favorites_manager",
    "navigation_history",
    "shortcut_manager",
    "breadcrumb_engine",
    "navigation_dashboard",
)

NAV_SURFACES = ("main", "sidebar", "top", "context", "module", "workspace")
MENU_FEATURES = ("dynamic", "nested", "mega", "module_groups", "permissions_based", "tenant_aware")
COMMAND_KINDS = (
    "open_module",
    "open_dashboard",
    "open_report",
    "open_ai_agent",
    "create_entity",
    "run_workflow",
    "execute_command",
    "search_everything",
)
SEARCH_CATEGORIES = (
    "modules",
    "users",
    "organizations",
    "projects",
    "documents",
    "crm",
    "erp",
    "finance",
    "hr",
    "ai_agents",
    "workflows",
    "reports",
    "tasks",
    "marketplace",
)
SEARCH_MODES = ("fuzzy", "exact", "semantic_ready")
PERFORMANCE = (
    "lazy_loading",
    "route_prefetching",
    "search_caching",
    "virtual_lists",
    "background_index_updates",
)
HOTKEYS = ("Ctrl+K", "Cmd+K")

INTEGRATION_TARGETS = (
    "enterprise_hub",
    "authentication_ui",
    "workspace_platform",
    "design_system",
    "ai_orchestrator",
    "crm_platform",
    "erp_platform",
    "analytics_platform",
    "notification_center",
)

KPI_TARGETS = {
    "unified_navigation": True,
    "command_palette_ready": True,
    "global_search_ready": True,
    "dynamic_menu": True,
    "favorites_ready": True,
    "navigation_history": True,
    "custom_shortcuts": True,
    "search_index_ready": True,
}

PRINCIPLES = (
    "instant_access_anywhere",
    "palette_first_navigation",
    "realtime_global_search",
    "permission_aware_menus",
    "high_performance_index",
    "phase3_navigation_platform",
)
