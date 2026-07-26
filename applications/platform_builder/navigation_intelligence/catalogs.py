"""Enterprise Navigation Intelligence catalogs — Sprint 29.14."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "engine", "title": "Navigation Intelligence Engine", "index": 1},
    {"id": "graph", "title": "Global Navigation Graph", "index": 2},
    {"id": "context", "title": "Context Aware Navigation", "index": 3},
    {"id": "recommendations", "title": "Smart Recommendations", "index": 4},
    {"id": "history", "title": "Navigation History", "index": 5},
    {"id": "quick_access", "title": "Quick Access", "index": 6},
    {"id": "cross_platform", "title": "Cross Platform Navigation", "index": 7},
    {"id": "search_routing", "title": "Intelligent Search Routing", "index": 8},
    {"id": "performance", "title": "Performance", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

NAVIGATION_INTELLIGENCE_COMPONENTS = (
    "Navigation Intelligence Engine",
    "Navigation Registry",
    "Navigation Context Engine",
    "Recommendation Engine",
    "Navigation API",
)

NAVIGATION_GRAPHS = (
    "Workspace Graph",
    "Module Graph",
    "Document Graph",
    "AI Graph",
    "Organization Graph",
    "Knowledge Graph",
    "Workflow Graph",
)

CONTEXT_SIGNALS = (
    "Current Organization",
    "Current Department",
    "Current Project",
    "Current Workflow",
    "Current AI Team",
    "Current User Intent",
)

RECOMMENDATION_TYPES = (
    "Next Workspace",
    "Related Documents",
    "Related AI Agents",
    "Related Dashboards",
    "Related Projects",
    "Related Knowledge",
    "Related Tasks",
)

HISTORY_FEATURES = (
    "Navigation Timeline",
    "Visited Modules",
    "Recent Projects",
    "Recent Organizations",
    "Favorites",
    "Pinned Locations",
)

QUICK_ACCESS_FEATURES = (
    "Favorites",
    "Bookmarks",
    "Pinned Dashboards",
    "Pinned AI Agents",
    "Pinned Workspaces",
    "Recent Commands",
)

CROSS_PLATFORM_TARGETS = (
    "Workspace OS",
    "Builder Studio",
    "Executive Dashboard",
    "AI Operations Center",
    "Knowledge Center",
    "Marketplace",
    "Administration",
    "Analytics",
)

SEARCH_ROUTES = (
    "Knowledge",
    "Documents",
    "Projects",
    "Organizations",
    "AI Agents",
    "Commands",
    "Marketplace",
)

PERFORMANCE_FEATURES = (
    "Navigation Cache",
    "Fast Index",
    "Context Cache",
    "Lazy Navigation",
    "Realtime Suggestions",
)

UI_SURFACES = (
    "Navigation Hub",
    "Quick Access Panel",
    "Context Navigator",
    "Recommendation Sidebar",
    "Navigation Timeline",
    "Smart Breadcrumbs",
)

GRAPH_NODES = {
    "Workspace Graph": ("Manager Workspace", "Executive Workspace", "Builder Workspace"),
    "Module Graph": ("AI Operations Center", "AI Team Map", "Visual Intelligence"),
    "Document Graph": ("Policy Pack", "Release Notes", "Runbook"),
    "AI Graph": ("Concierge", "Ops Agent", "Knowledge Agent"),
    "Organization Graph": ("HQ", "Ops Dept", "Product Dept"),
    "Knowledge Graph": ("Architecture", "Sprints", "Playbooks"),
    "Workflow Graph": ("Onboarding", "Release", "Incident Response"),
}


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "components": list(NAVIGATION_INTELLIGENCE_COMPONENTS),
        "graphs": list(NAVIGATION_GRAPHS),
        "context_signals": list(CONTEXT_SIGNALS),
        "recommendation_types": list(RECOMMENDATION_TYPES),
        "history_features": list(HISTORY_FEATURES),
        "quick_access_features": list(QUICK_ACCESS_FEATURES),
        "cross_platform_targets": list(CROSS_PLATFORM_TARGETS),
        "search_routes": list(SEARCH_ROUTES),
        "performance_features": list(PERFORMANCE_FEATURES),
        "ui_surfaces": list(UI_SURFACES),
        "graph_nodes": {k: list(v) for k, v in GRAPH_NODES.items()},
        "enterprise_design_system": True,
        "dark_mode": True,
        "responsive": True,
        "workspace_os_integration": True,
        "command_center_integration": True,
        "ai_native": True,
        "executes_business_logic": False,
        "verified_context_only": True,
    }
