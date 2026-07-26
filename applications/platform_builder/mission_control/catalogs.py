"""Enterprise Mission Control catalogs — Sprint 29.19."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "core", "title": "Mission Control Core", "index": 1},
    {"id": "operations", "title": "Unified Operations View", "index": 2},
    {"id": "overview", "title": "Executive Overview", "index": 3},
    {"id": "activity", "title": "Global Activity", "index": 4},
    {"id": "panels", "title": "Mission Panels", "index": 5},
    {"id": "decisions", "title": "Decision Center", "index": 6},
    {"id": "resources", "title": "Resource Command View", "index": 7},
    {"id": "timeline", "title": "Mission Timeline", "index": 8},
    {"id": "performance", "title": "Performance", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

MISSION_COMPONENTS = (
    "Mission Control Engine",
    "Mission Registry",
    "Mission Dashboard",
    "Mission Coordinator",
    "Mission API",
)

OPERATIONS_SOURCES = (
    "Workspace OS",
    "Command Center",
    "Digital Twin",
    "Digital Twin Intelligence",
    "Strategy Engine",
    "Workflow Intelligence",
    "Navigation Intelligence",
    "Visual Intelligence",
    "Knowledge Intelligence",
)

HEALTH_DIMENSIONS = (
    "Organization Status",
    "Operational Health",
    "Strategic Health",
    "Knowledge Health",
    "AI Health",
    "Infrastructure Health",
    "Platform Health",
)

ACTIVITY_STREAMS = (
    "Live Organization Events",
    "Workflow Activity",
    "AI Activity",
    "Knowledge Updates",
    "Infrastructure Events",
    "Executive Timeline",
)

MISSION_PANELS = (
    "Executive Summary",
    "Critical Alerts",
    "Risk Center",
    "Opportunity Center",
    "Recommendations",
    "Organization Overview",
)

DECISION_FEATURES = (
    "Decision Context",
    "Alternative Options",
    "Risk Comparison",
    "Impact Comparison",
    "Dependencies",
    "Supporting Evidence",
)

RESOURCE_VIEWS = (
    "Departments",
    "Projects",
    "AI Teams",
    "Infrastructure",
    "Knowledge Resources",
    "Platform Services",
)

TIMELINE_SEGMENTS = (
    "Live Timeline",
    "Strategic Timeline",
    "Milestones",
    "Incidents",
    "Completed Objectives",
    "Future Objectives",
)

PERFORMANCE_FEATURES = (
    "Realtime Aggregation",
    "Incremental Refresh",
    "Distributed Cache",
    "High Availability",
    "Large Enterprise Optimization",
)

UI_SURFACES = (
    "Mission Control Home",
    "Executive Operations Center",
    "Mission Timeline",
    "Executive Cockpit",
    "Strategic Overview",
    "Operational Overview",
    "Risk Center",
    "Recommendation Center",
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "components": list(MISSION_COMPONENTS),
        "operations_sources": list(OPERATIONS_SOURCES),
        "health_dimensions": list(HEALTH_DIMENSIONS),
        "activity_streams": list(ACTIVITY_STREAMS),
        "mission_panels": list(MISSION_PANELS),
        "decision_features": list(DECISION_FEATURES),
        "resource_views": list(RESOURCE_VIEWS),
        "timeline_segments": list(TIMELINE_SEGMENTS),
        "performance_features": list(PERFORMANCE_FEATURES),
        "ui_surfaces": list(UI_SURFACES),
        "enterprise_design_system": True,
        "dark_mode": True,
        "responsive": True,
        "realtime": True,
        "enterprise_scale": True,
        "read_only_aggregation_layer": True,
        "executes_business_logic": False,
        "owns_business_logic": False,
        "replaces_existing_modules": False,
        "aggregates_existing_platform_services": True,
    }
