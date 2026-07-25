"""Visual Intelligence Engine catalogs — Sprint 29.10."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "engine", "title": "Visual Intelligence Engine", "index": 1},
    {"id": "patterns", "title": "Pattern Detection", "index": 2},
    {"id": "anomalies", "title": "Anomaly Detection", "index": 3},
    {"id": "attention", "title": "Attention Recommendations", "index": 4},
    {"id": "executive", "title": "Executive Insights", "index": 5},
    {"id": "heatmaps", "title": "Visual Heatmaps", "index": 6},
    {"id": "trends", "title": "Trend Engine", "index": 7},
    {"id": "health", "title": "Visual Health Index", "index": 8},
    {"id": "predictive", "title": "Predictive Visualization Foundation", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

INTELLIGENCE_COMPONENTS = (
    "Visual Intelligence Engine",
    "Insight Engine",
    "Pattern Engine",
    "Recommendation Engine",
    "Analytics Registry",
)

PATTERN_TYPES = (
    "Activity Trends",
    "Workflow Patterns",
    "Knowledge Patterns",
    "Department Patterns",
    "AI Collaboration Patterns",
    "Organization Growth Patterns",
)

ANOMALY_TYPES = (
    "Inactive AI",
    "Workflow Bottlenecks",
    "Queue Congestion",
    "Knowledge Gaps",
    "Communication Delays",
    "Resource Imbalance",
    "Unusual Activity",
)

ATTENTION_RECOMMENDATIONS = (
    "Critical Departments",
    "Important Workflows",
    "Priority Documents",
    "Executive Alerts",
    "Key Decisions",
    "High Impact Events",
)

EXECUTIVE_INSIGHTS = (
    "Daily Overview",
    "Weekly Summary",
    "Monthly Growth",
    "Organization Health",
    "Department Performance",
    "AI Productivity",
    "Knowledge Health",
)

HEATMAP_TYPES = (
    "Activity Heatmap",
    "Department Heatmap",
    "Knowledge Heatmap",
    "Workflow Heatmap",
    "Organization Heatmap",
    "Future AI City Heatmap",
)

TREND_TYPES = (
    "Growth Trends",
    "Performance Trends",
    "Knowledge Evolution",
    "AI Utilization",
    "Organization Development",
)

HEALTH_INDICES = (
    "Organization Health",
    "Department Health",
    "Workflow Health",
    "Knowledge Health",
    "AI Health",
    "Overall Platform Health",
)

PREDICTIVE_APIS = (
    "Capacity Forecast",
    "Growth Forecast",
    "Load Forecast",
    "Risk Visualization",
    "Resource Forecast",
    "Future Expansion",
)

UI_SURFACES = (
    "Insight Center",
    "Executive Dashboard",
    "Health Overview",
    "Recommendation Panel",
    "Trend Explorer",
    "Heatmap Viewer",
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "components": list(INTELLIGENCE_COMPONENTS),
        "pattern_types": list(PATTERN_TYPES),
        "anomaly_types": list(ANOMALY_TYPES),
        "attention_recommendations": list(ATTENTION_RECOMMENDATIONS),
        "executive_insights": list(EXECUTIVE_INSIGHTS),
        "heatmap_types": list(HEATMAP_TYPES),
        "trend_types": list(TREND_TYPES),
        "health_indices": list(HEALTH_INDICES),
        "predictive_apis": list(PREDICTIVE_APIS),
        "ui_surfaces": list(UI_SURFACES),
        "changes_business_logic": False,
        "generates_business_events": False,
        "analyzes_verified_events_only": True,
        "produces_visual_recommendations_only": True,
        "autonomous_business_decisions": False,
        "enterprise_design_system": True,
        "dark_mode": True,
        "responsive": True,
        "gpu_optimized": True,
        "visual_layer": True,
        "visual_event_bus": True,
    }
