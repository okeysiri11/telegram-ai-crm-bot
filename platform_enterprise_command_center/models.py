"""Enterprise Command Center constants — Sprint 26.6."""

from __future__ import annotations

CC_PATH = "src/web/command-center"
VERSION = "9.1.0-rc1"
API_PREFIX = "/api/enterprise-command/v1"

ARCHITECTURE = (
    "universal_command_palette",
    "global_omnibox",
    "quick_actions_engine",
    "productivity_hub",
    "ai_command_center",
    "smart_suggestions",
    "context_engine",
    "keyboard_productivity",
    "command_analytics",
    "enterprise_navigation_index",
    "security_rbac_gate",
    "command_dashboard",
)

COMMAND_KINDS = (
    "navigate",
    "search",
    "create",
    "open",
    "ai_execute",
    "run_workflow",
    "run_automation",
    "open_module",
    "open_dashboard",
    "open_report",
    "open_settings",
    "mass_update",
)

OMNIBOX_SOURCES = (
    "crm",
    "erp",
    "knowledge",
    "documents",
    "projects",
    "tasks",
    "users",
    "organizations",
    "ai_agents",
    "workflows",
    "marketplace",
    "applications",
    "verticals",
    "dashboards",
    "reports",
    "settings",
    "modules",
)

RANKING_SIGNALS = (
    "relevance",
    "recency",
    "frequency",
    "permissions",
    "workspace",
    "organization",
    "ai_confidence",
)

QUICK_ACTIONS = (
    "create_client",
    "create_lead",
    "create_company",
    "create_project",
    "create_task",
    "create_workflow",
    "create_automation",
    "create_ai_agent",
    "create_dashboard",
    "create_document",
    "open_crm",
    "open_erp",
    "open_marketplace",
    "open_ai_studio",
    "open_knowledge",
    "open_reports",
    "open_analytics",
    "open_settings",
)

PRODUCTIVITY_WIDGETS = (
    "recent_activity",
    "pinned_objects",
    "favorites",
    "drafts",
    "clipboard_history",
    "notifications",
    "reminder_center",
    "scheduled_actions",
    "quick_notes",
    "recently_opened",
    "recent_searches",
    "most_used_commands",
)

AI_COMMANDS = (
    "open_crm",
    "open_erp",
    "open_beauty",
    "open_auto",
    "open_agro",
    "open_marketplace",
    "open_dashboard",
    "find_client",
    "find_employee",
    "create_customer",
    "generate_weekly_report",
    "launch_workflow",
    "run_automation",
    "create_invoice",
    "open_document",
    "mass_update_records",
    "summarize_workspace",
)

HOTKEYS = (
    "Ctrl+K",
    "Cmd+K",
    "Ctrl+P",
    "Ctrl+Shift+P",
    "Ctrl+Space",
    "Ctrl+/",
    "Esc",
    "Enter",
    "ArrowUp",
    "ArrowDown",
    "Tab",
    "Shift+Tab",
)

NAV_INDEX_TYPES = (
    "applications",
    "modules",
    "dashboards",
    "pages",
    "routes",
    "ai_agents",
    "workflows",
    "marketplace",
    "knowledge",
    "crm",
    "erp",
    "reports",
    "analytics",
    "settings",
    "widgets",
)

SECURITY_GATES = (
    "rbac",
    "tenant_isolation",
    "workspace_access",
    "organization_access",
    "audit_log",
)

INTEGRATION_TARGETS = (
    "enterprise_hub",
    "workspace_platform",
    "navigation_platform",
    "dashboard_engine",
    "ai_orchestrator",
    "marketplace",
    "identity_center",
    "design_system",
    "crm_platform",
    "erp_platform",
)

KPI_TARGETS = {
    "command_palette_ready": True,
    "omnibox_ready": True,
    "quick_actions_ready": True,
    "productivity_hub_ready": True,
    "ai_command_center_ready": True,
    "smart_suggestions_ready": True,
    "context_engine_ready": True,
    "keyboard_productivity_ready": True,
    "command_analytics_ready": True,
    "navigation_index_ready": True,
    "security_gates_ready": True,
}

PRINCIPLES = (
    "keyboard_first",
    "zero_latency_search",
    "permission_aware_execution",
    "context_aware_ai",
    "fuzzy_instant_match",
    "enterprise_productivity",
    "phase3_command_center",
)
