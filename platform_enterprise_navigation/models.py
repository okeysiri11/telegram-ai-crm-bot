"""Navigation Platform constants — Sprint 26.7."""

from __future__ import annotations

NAV_PATH = "src/web/navigation"
VERSION = "9.4.0"
API_PREFIX = "/api/enterprise-navigation/v1"

ARCHITECTURE = (
    "global_navigation",
    "workspace_federation",
    "application_registry",
    "global_search",
    "smart_favorites",
    "recent_history",
    "enterprise_breadcrumbs",
    "quick_switcher",
    "navigation_analytics",
    "security_rbac_gate",
    "navigation_manager",
    "menu_engine",
    "command_palette",
    "search_index",
    "search_provider",
    "shortcut_manager",
    "navigation_dashboard",
)

NAV_SURFACES = ("main", "sidebar", "top", "context", "module", "workspace")
GLOBAL_NAV_SECTIONS = (
    "applications",
    "verticals",
    "crm",
    "erp",
    "finance",
    "analytics",
    "marketplace",
    "knowledge",
    "ai_studio",
    "dashboards",
    "reports",
    "settings",
    "automations",
    "workflows",
    "documents",
)

WORKSPACE_KINDS = (
    "personal",
    "organization",
    "department",
    "project",
    "customer",
    "ai",
    "temporary",
)

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
    "switch_workspace",
    "quick_switch",
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
    "applications",
    "dashboards",
    "widgets",
    "knowledge",
)
SEARCH_MODES = ("fuzzy", "exact", "semantic_ready")
PERFORMANCE = (
    "lazy_loading",
    "route_prefetching",
    "search_caching",
    "virtual_lists",
    "background_index_updates",
)
HOTKEYS = ("Ctrl+K", "Cmd+K", "Ctrl+Tab", "Ctrl+Shift+Tab")

FAVORITE_KINDS = (
    "page",
    "dashboard",
    "report",
    "customer",
    "project",
    "command",
    "ai_agent",
    "document",
    "search",
)

HISTORY_KINDS = (
    "page",
    "search",
    "document",
    "report",
    "ai_chat",
    "command",
)

QUICK_SWITCH_TARGETS = (
    "applications",
    "dashboards",
    "workspaces",
    "ai_chats",
    "documents",
)

SECURITY_GATES = (
    "rbac",
    "workspace_isolation",
    "tenant_isolation",
    "organization_isolation",
)

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
    "command_center",
    "marketplace",
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
    "workspace_federation_ready": True,
    "application_registry_ready": True,
    "smart_favorites_ready": True,
    "enterprise_breadcrumbs_ready": True,
    "quick_switcher_ready": True,
    "navigation_analytics_ready": True,
}

PRINCIPLES = (
    "instant_access_anywhere",
    "palette_first_navigation",
    "realtime_global_search",
    "permission_aware_menus",
    "high_performance_index",
    "workspace_federation",
    "unified_discoverability",
    "phase3_navigation_platform",
    "phase3_navigation_federation",
)
