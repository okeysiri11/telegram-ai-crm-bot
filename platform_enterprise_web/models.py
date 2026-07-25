"""Web Foundation constants — Sprint 26.1."""

from __future__ import annotations

STACK = (
    "react_19",
    "typescript",
    "vite",
    "tailwind_css",
    "tanstack_query",
    "react_router",
    "zustand",
    "react_hook_form",
    "zod",
    "chart_js",
    "socket_io_client",
)

SHELL_CAPABILITIES = (
    "bootstrap",
    "routing",
    "error_boundary",
    "loading_screen",
    "global_providers",
    "configuration_loader",
    "session_manager",
)

AUTH_CAPABILITIES = (
    "login",
    "logout",
    "session_restore",
    "jwt",
    "refresh_token",
    "mfa_ready",
    "tenant_selection",
    "user_profile",
)

LAYOUTS = (
    "full",
    "dashboard",
    "workspace",
    "authentication",
    "empty",
)

NAVIGATION = (
    "sidebar",
    "top_navigation",
    "breadcrumbs",
    "quick_search",
    "favorites",
    "recent_pages",
    "module_navigation",
)

UI_COMPONENTS = (
    "button",
    "input",
    "select",
    "checkbox",
    "switch",
    "radio",
    "modal",
    "dialog",
    "drawer",
    "tabs",
    "card",
    "badge",
    "avatar",
    "tooltip",
    "dropdown",
    "table",
    "pagination",
    "date_picker",
    "data_grid",
    "charts",
    "notifications",
)

LOCALES = ("en", "ru", "uk")

DASHBOARD_WIDGETS = (
    "ai_assistant",
    "active_tasks",
    "calendar",
    "notifications",
    "kpis",
    "recent_activity",
    "favorites",
    "system_health",
)

INTEGRATION_TARGETS = (
    "enterprise_hub",
    "authentication",
    "ai_orchestrator",
    "workflow",
    "notifications",
    "monitoring",
    "knowledge_graph",
    "marketplace",
)

KPI_TARGETS = {
    "web_shell_ready": True,
    "navigation_ready": True,
    "ui_library_ready": True,
    "auth_ready": True,
    "multi_tenant_ready": True,
    "themes_localization_ready": True,
    "dashboard_ready": True,
    "modules_plug_in_without_arch_change": True,
}

PRINCIPLES = (
    "unified_enterprise_web_shell",
    "modular_plugin_ready",
    "multi_tenant_first",
    "additive_to_platform_console",
    "no_duplicated_business_logic",
    "phase3_foundation",
)

WEB_PATH = "src/web"
