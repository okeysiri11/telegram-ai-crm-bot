"""Enterprise Digital Twin catalogs — Sprint 29.16."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "core", "title": "Digital Twin Core", "index": 1},
    {"id": "organization", "title": "Organization Mirror", "index": 2},
    {"id": "ai", "title": "AI Mirror", "index": 3},
    {"id": "workflow", "title": "Workflow Mirror", "index": 4},
    {"id": "knowledge", "title": "Knowledge Mirror", "index": 5},
    {"id": "resource", "title": "Resource Mirror", "index": 6},
    {"id": "snapshot", "title": "Snapshot Engine", "index": 7},
    {"id": "comparison", "title": "State Comparison", "index": 8},
    {"id": "performance", "title": "Performance", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

DIGITAL_TWIN_COMPONENTS = (
    "Digital Twin Engine",
    "Twin Registry",
    "Twin Synchronization Engine",
    "Twin Snapshot Manager",
    "Twin API",
)

ORGANIZATION_MIRROR_ENTITIES = (
    "Organizations",
    "Departments",
    "Business Units",
    "Projects",
    "Teams",
    "Users",
    "Roles",
)

AI_MIRROR_ENTITIES = (
    "AI Organizations",
    "AI Teams",
    "AI Specialists",
    "AI Supervisors",
    "AI Collaboration",
    "AI Health",
    "AI Activity",
)

WORKFLOW_MIRROR_ENTITIES = (
    "Running Workflows",
    "Workflow Status",
    "Workflow Dependencies",
    "Critical Paths",
    "Approval Chains",
    "Execution Progress",
)

KNOWLEDGE_MIRROR_ENTITIES = (
    "Knowledge Graph",
    "Knowledge Flow",
    "Knowledge Health",
    "Knowledge Sources",
    "Knowledge Relationships",
)

RESOURCE_MIRROR_ENTITIES = (
    "Infrastructure",
    "Compute Resources",
    "Storage",
    "API Services",
    "Queues",
    "Caches",
    "Background Workers",
)

SNAPSHOT_TYPES = (
    "Realtime Snapshot",
    "Historical Snapshot",
    "Version Snapshot",
    "Comparison Snapshot",
    "Restore Reference",
)

COMPARISON_DIMENSIONS = (
    "Organization Versions",
    "Workflow Changes",
    "Knowledge Evolution",
    "AI Growth",
    "Infrastructure Changes",
)

PERFORMANCE_FEATURES = (
    "Incremental Sync",
    "Realtime Updates",
    "Delta Synchronization",
    "Distributed Cache",
    "Scalable Twin Graph",
)

UI_SURFACES = (
    "Digital Twin Center",
    "Organization Mirror",
    "AI Mirror",
    "Workflow Mirror",
    "Knowledge Mirror",
    "Infrastructure Mirror",
    "Snapshot Browser",
    "Comparison Viewer",
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "components": list(DIGITAL_TWIN_COMPONENTS),
        "organization_mirror": list(ORGANIZATION_MIRROR_ENTITIES),
        "ai_mirror": list(AI_MIRROR_ENTITIES),
        "workflow_mirror": list(WORKFLOW_MIRROR_ENTITIES),
        "knowledge_mirror": list(KNOWLEDGE_MIRROR_ENTITIES),
        "resource_mirror": list(RESOURCE_MIRROR_ENTITIES),
        "snapshot_types": list(SNAPSHOT_TYPES),
        "comparison_dimensions": list(COMPARISON_DIMENSIONS),
        "performance_features": list(PERFORMANCE_FEATURES),
        "ui_surfaces": list(UI_SURFACES),
        "enterprise_design_system": True,
        "dark_mode": True,
        "responsive": True,
        "realtime": True,
        "enterprise_scale": True,
        "read_only_reflection_layer": True,
        "executes_business_logic": False,
        "owns_business_logic": False,
        "mirrors_verified_platform_state": True,
    }
