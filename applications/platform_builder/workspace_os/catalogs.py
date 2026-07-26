"""Enterprise Workspace OS catalogs — Sprint 29.12."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "core", "title": "Workspace OS Core", "index": 1},
    {"id": "types", "title": "Workspace Types", "index": 2},
    {"id": "layout", "title": "Layout Engine", "index": 3},
    {"id": "session", "title": "Session Management", "index": 4},
    {"id": "modules", "title": "Module Integration", "index": 5},
    {"id": "context", "title": "Context Engine", "index": 6},
    {"id": "multitasking", "title": "Multitasking", "index": 7},
    {"id": "search", "title": "Workspace Search", "index": 8},
    {"id": "performance", "title": "Performance", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

WORKSPACE_OS_COMPONENTS = (
    "Workspace OS",
    "Workspace Kernel",
    "Workspace Registry",
    "Workspace Manager",
    "Workspace API",
)

WORKSPACE_TYPES = (
    "Executive Workspace",
    "Manager Workspace",
    "Operator Workspace",
    "Developer Workspace",
    "Builder Workspace",
    "Analytics Workspace",
    "Support Workspace",
    "Organization Workspace",
)

LAYOUT_FEATURES = (
    "Dockable Panels",
    "Resizable Panels",
    "Floating Windows",
    "Split View",
    "Workspace Templates",
    "Persistent Layouts",
)

SESSION_FEATURES = (
    "Workspace Restore",
    "Session Restore",
    "Open Tabs",
    "Pinned Modules",
    "Active Context",
    "Recent Activity",
)

INTEGRATED_MODULES = (
    "AI Operations Center",
    "Executive Dashboard",
    "AI Team Map",
    "Builder Studio",
    "Knowledge Center",
    "Analytics Center",
    "Marketplace",
    "Administration",
)

CONTEXT_LAYERS = (
    "Organization Context",
    "Department Context",
    "Project Context",
    "Workflow Context",
    "AI Context",
    "User Context",
)

MULTITASKING_FEATURES = (
    "Multiple Workspaces",
    "Background Tasks",
    "Live Synchronization",
    "Cross Workspace Navigation",
    "Shared Clipboard API",
)

SEARCH_SCOPES = (
    "Global Search",
    "Module Search",
    "AI Search",
    "Document Search",
    "Command Search",
)

PERFORMANCE_FEATURES = (
    "Workspace Cache",
    "Lazy Module Loading",
    "Memory Optimization",
    "Context Optimization",
    "Background Cleanup",
)

UI_SURFACES = (
    "Workspace Launcher",
    "Workspace Switcher",
    "Context Bar",
    "Session Manager",
    "Layout Editor",
    "Workspace Library",
)

LAYOUT_TEMPLATES = {
    "Executive Workspace": {"panels": ["summary", "kpis", "alerts"], "split": "horizontal"},
    "Manager Workspace": {"panels": ["team", "pipeline", "calendar"], "split": "grid"},
    "Operator Workspace": {"panels": ["console", "queue", "status"], "split": "vertical"},
    "Developer Workspace": {"panels": ["code", "logs", "docs"], "split": "ide"},
    "Builder Workspace": {"panels": ["wizard", "preview", "help"], "split": "builder"},
    "Analytics Workspace": {"panels": ["charts", "filters", "exports"], "split": "analytics"},
    "Support Workspace": {"panels": ["tickets", "kb", "chat"], "split": "support"},
    "Organization Workspace": {"panels": ["org_map", "roles", "policies"], "split": "org"},
}


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "components": list(WORKSPACE_OS_COMPONENTS),
        "workspace_types": list(WORKSPACE_TYPES),
        "layout_features": list(LAYOUT_FEATURES),
        "session_features": list(SESSION_FEATURES),
        "integrated_modules": list(INTEGRATED_MODULES),
        "context_layers": list(CONTEXT_LAYERS),
        "multitasking_features": list(MULTITASKING_FEATURES),
        "search_scopes": list(SEARCH_SCOPES),
        "performance_features": list(PERFORMANCE_FEATURES),
        "ui_surfaces": list(UI_SURFACES),
        "layout_templates": {k: dict(v) for k, v in LAYOUT_TEMPLATES.items()},
        "enterprise_design_system": True,
        "dark_mode": True,
        "responsive": True,
        "high_performance": True,
        "multi_workspace": True,
        "role_aware": True,
        "executes_business_logic": False,
        "unified_operating_environment": True,
    }
