"""Enterprise Strategy Engine catalogs — Sprint 29.18."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "core", "title": "Strategy Engine Core", "index": 1},
    {"id": "sources", "title": "Data Sources", "index": 2},
    {"id": "overview", "title": "Strategic Overview", "index": 3},
    {"id": "priorities", "title": "Strategic Priorities", "index": 4},
    {"id": "recommendations", "title": "Executive Recommendations", "index": 5},
    {"id": "scorecard", "title": "Enterprise Scorecard", "index": 6},
    {"id": "timeline", "title": "Executive Timeline", "index": 7},
    {"id": "decisions", "title": "Decision Support", "index": 8},
    {"id": "performance", "title": "Performance", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

STRATEGY_COMPONENTS = (
    "Strategy Engine",
    "Strategy Registry",
    "Strategy API",
    "Strategy Coordinator",
    "Executive Strategy Service",
)

DATA_SOURCES = (
    "Digital Twin Intelligence",
    "Workflow Intelligence",
    "Navigation Intelligence",
    "Visual Intelligence",
    "Knowledge Intelligence",
    "Executive Dashboard",
    "Organization Analytics",
)

OVERVIEW_SURFACES = (
    "Organization Overview",
    "Business Overview",
    "Operational Overview",
    "Technology Overview",
    "Knowledge Overview",
    "AI Overview",
)

PRIORITY_CATEGORIES = (
    "Critical Objectives",
    "High Priority Projects",
    "Operational Risks",
    "Growth Opportunities",
    "Infrastructure Priorities",
    "Knowledge Priorities",
)

RECOMMENDATION_TYPES = (
    "Priority Recommendations",
    "Optimization Recommendations",
    "Scaling Recommendations",
    "Risk Mitigation Suggestions",
    "Resource Allocation Suggestions",
    "Architecture Suggestions",
)

SCORECARD_METRICS = (
    "Strategic Health",
    "Execution Health",
    "Organization Maturity",
    "Knowledge Maturity",
    "AI Maturity",
    "Platform Maturity",
)

TIMELINE_SEGMENTS = (
    "Completed Milestones",
    "Current Initiatives",
    "Upcoming Objectives",
    "Strategic Roadmap",
)

DECISION_SUPPORT_FEATURES = (
    "Decision Context",
    "Alternative Options",
    "Impact Comparison",
    "Risk Comparison",
    "Dependency Overview",
)

PERFORMANCE_FEATURES = (
    "Incremental Aggregation",
    "Realtime Updates",
    "Caching",
    "Distributed Strategy Graph",
    "High Availability",
)

UI_SURFACES = (
    "Executive Strategy Center",
    "Enterprise Scorecard",
    "Strategic Roadmap",
    "Decision Support Panel",
    "Priority Matrix",
    "Executive Insights",
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "components": list(STRATEGY_COMPONENTS),
        "data_sources": list(DATA_SOURCES),
        "overview_surfaces": list(OVERVIEW_SURFACES),
        "priority_categories": list(PRIORITY_CATEGORIES),
        "recommendation_types": list(RECOMMENDATION_TYPES),
        "scorecard_metrics": list(SCORECARD_METRICS),
        "timeline_segments": list(TIMELINE_SEGMENTS),
        "decision_support_features": list(DECISION_SUPPORT_FEATURES),
        "performance_features": list(PERFORMANCE_FEATURES),
        "ui_surfaces": list(UI_SURFACES),
        "enterprise_design_system": True,
        "dark_mode": True,
        "responsive": True,
        "realtime": True,
        "enterprise_scale": True,
        "read_only_strategy_layer": True,
        "executes_business_logic": False,
        "changes_platform_state": False,
        "aggregates_existing_intelligence": True,
    }
