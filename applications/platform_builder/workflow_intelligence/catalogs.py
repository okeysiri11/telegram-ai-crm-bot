"""Enterprise Workflow Intelligence OS catalogs — Sprint 29.15."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "core", "title": "Workflow Intelligence Core", "index": 1},
    {"id": "graph", "title": "Global Workflow Graph", "index": 2},
    {"id": "dependencies", "title": "Dependency Analysis", "index": 3},
    {"id": "bottlenecks", "title": "Bottleneck Detection", "index": 4},
    {"id": "critical_path", "title": "Critical Path Engine", "index": 5},
    {"id": "resources", "title": "Resource Coordination", "index": 6},
    {"id": "recommendations", "title": "Workflow Recommendations", "index": 7},
    {"id": "orchestration", "title": "Enterprise Orchestration", "index": 8},
    {"id": "performance", "title": "Performance", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

WORKFLOW_INTELLIGENCE_COMPONENTS = (
    "Workflow Intelligence Engine",
    "Workflow Registry",
    "Workflow Dependency Engine",
    "Workflow Analytics API",
    "Workflow Recommendation Engine",
)

WORKFLOW_GRAPH_TYPES = (
    "Organization Workflows",
    "Department Workflows",
    "Project Workflows",
    "AI Workflows",
    "Approval Chains",
    "Automation Chains",
    "Cross Organization Dependencies",
)

DEPENDENCY_TYPES = (
    "Workflow Dependencies",
    "Task Dependencies",
    "Document Dependencies",
    "Knowledge Dependencies",
    "AI Dependencies",
    "Resource Dependencies",
)

BOTTLENECK_TYPES = (
    "Approval Delays",
    "Queue Congestion",
    "Idle Workflows",
    "Resource Conflicts",
    "Missing Dependencies",
    "Long Running Processes",
)

CRITICAL_PATH_FEATURES = (
    "Critical Workflow",
    "Blocking Tasks",
    "Execution Order",
    "Parallel Opportunities",
    "Estimated Completion",
)

RESOURCE_CAPACITY_TYPES = (
    "Department Capacity",
    "AI Capacity",
    "Human Capacity",
    "Infrastructure Load",
    "Execution Balance",
)

RECOMMENDATION_TYPES = (
    "Workflow Optimization",
    "Parallel Execution",
    "Dependency Resolution",
    "Resource Redistribution",
    "Priority Adjustments",
)

ORCHESTRATION_TARGETS = (
    "Builder Studio",
    "Knowledge Center",
    "AI Operations Center",
    "Executive Dashboard",
    "Workspace OS",
    "Marketplace",
    "Analytics",
)

PERFORMANCE_FEATURES = (
    "Workflow Cache",
    "Dependency Cache",
    "Realtime Graph Updates",
    "Incremental Analysis",
    "Large Scale Optimization",
)

UI_SURFACES = (
    "Workflow Intelligence Center",
    "Dependency Explorer",
    "Critical Path Viewer",
    "Resource Monitor",
    "Workflow Recommendations",
)

SAMPLE_WORKFLOWS = {
    "Organization Workflows": ("Org Onboarding", "Policy Rollout"),
    "Department Workflows": ("Ops Intake", "Support Escalation"),
    "Project Workflows": ("Release Pipeline", "Feature Delivery"),
    "AI Workflows": ("Agent Handoff", "Concierge Review"),
    "Approval Chains": ("Budget Approval", "Access Approval"),
    "Automation Chains": ("Nightly Sync", "Alert Fanout"),
    "Cross Organization Dependencies": ("Partner Sync", "Federation Gate"),
}


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "components": list(WORKFLOW_INTELLIGENCE_COMPONENTS),
        "graph_types": list(WORKFLOW_GRAPH_TYPES),
        "dependency_types": list(DEPENDENCY_TYPES),
        "bottleneck_types": list(BOTTLENECK_TYPES),
        "critical_path_features": list(CRITICAL_PATH_FEATURES),
        "resource_capacity_types": list(RESOURCE_CAPACITY_TYPES),
        "recommendation_types": list(RECOMMENDATION_TYPES),
        "orchestration_targets": list(ORCHESTRATION_TARGETS),
        "performance_features": list(PERFORMANCE_FEATURES),
        "ui_surfaces": list(UI_SURFACES),
        "sample_workflows": {k: list(v) for k, v in SAMPLE_WORKFLOWS.items()},
        "enterprise_design_system": True,
        "dark_mode": True,
        "responsive": True,
        "workspace_os_integration": True,
        "command_center_integration": True,
        "navigation_intelligence_integration": True,
        "enterprise_scale": True,
        "executes_business_logic": False,
        "orchestrates_visibility_only": True,
    }
