"""God Mode / Platform Control Center catalogs — Sprint 28.7."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "overview", "title": "Global Platform Overview", "index": 1},
    {"id": "search", "title": "Global Search", "index": 2},
    {"id": "inspector", "title": "Object Inspector", "index": 3},
    {"id": "editor", "title": "Live Object Editor", "index": 4},
    {"id": "registry", "title": "Global Registry", "index": 5},
    {"id": "health", "title": "System Health", "index": 6},
    {"id": "diagnostics", "title": "Platform Diagnostics", "index": 7},
    {"id": "architecture", "title": "Architecture View", "index": 8},
    {"id": "audit", "title": "Audit Center", "index": 9},
    {"id": "explain", "title": "Explain Mode", "index": 10},
    {"id": "create", "title": "Create", "index": 11},
]

OVERVIEW_CATEGORIES = (
    "Organizations",
    "Users",
    "AI Specialists",
    "Concierges",
    "Verticals",
    "Departments",
    "Modules",
    "Knowledge",
    "Workflows",
    "Marketplace",
    "Registries",
    "Visual Layer",
)

SEARCH_SCOPES = (
    "AI",
    "Organizations",
    "Documents",
    "Knowledge",
    "Registry",
    "Users",
    "Dashboards",
    "Workflows",
    "Marketplace",
)

INSPECTOR_FIELDS = (
    "internal_id",
    "visual_id",
    "object_type",
    "owner",
    "dependencies",
    "relationships",
    "lifecycle",
    "status",
    "history",
)

EDITOR_FIELDS = (
    "properties",
    "permissions",
    "knowledge",
    "relationships",
    "dependencies",
    "metadata",
)

REGISTRY_ACTIONS = (
    "Browse",
    "Search",
    "Filter",
    "Repair",
    "Rebuild",
    "Synchronize",
)

HEALTH_METRICS = (
    "Services",
    "Modules",
    "Performance",
    "Registry Status",
    "Synchronization",
    "AI Status",
    "Memory Usage",
)

DIAGNOSTIC_CHECKS = (
    "Broken Links",
    "Missing Dependencies",
    "Registry Problems",
    "Invalid References",
    "Configuration Issues",
)

ARCHITECTURE_GRAPHS = (
    "Module Relationships",
    "AI Relationships",
    "Knowledge Flow",
    "Workflow Graph",
    "Registry Graph",
    "Future Visual Layer Graph",
)

EXPLAIN_FIELDS = (
    "reason",
    "expected_benefit",
    "business_impact",
    "alternative_options",
    "estimated_effect",
)

REGISTRY_NAMES = (
    "platform_builder_ai_registry",
    "platform_builder_concierge_registry",
    "platform_builder_platform_registry",
    "platform_builder_builder_registry",
    "vertical_registry",
    "visual_layers",
    "academy_progress",
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "overview_categories": list(OVERVIEW_CATEGORIES),
        "search_scopes": list(SEARCH_SCOPES),
        "inspector_fields": list(INSPECTOR_FIELDS),
        "editor_fields": list(EDITOR_FIELDS),
        "registry_actions": list(REGISTRY_ACTIONS),
        "health_metrics": list(HEALTH_METRICS),
        "diagnostic_checks": list(DIAGNOSTIC_CHECKS),
        "architecture_graphs": list(ARCHITECTURE_GRAPHS),
        "explain_fields": list(EXPLAIN_FIELDS),
        "registries": list(REGISTRY_NAMES),
        "access": {"platform_owner_only": True},
    }
