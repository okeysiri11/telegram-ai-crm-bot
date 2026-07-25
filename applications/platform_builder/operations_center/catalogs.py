"""AI Operations Center catalogs — Sprint 29.1."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "dashboard", "title": "Operations Dashboard", "index": 1},
    {"id": "live_status", "title": "Live Status Engine", "index": 2},
    {"id": "realtime_activity", "title": "Realtime Activity", "index": 3},
    {"id": "visual_ids", "title": "Visual ID Support", "index": 4},
    {"id": "wait_experience", "title": "Wait Experience Engine", "index": 5},
    {"id": "team_overview", "title": "Team Overview", "index": 6},
    {"id": "system_health", "title": "System Health", "index": 7},
    {"id": "ai_city_foundation", "title": "Foundation for AI City", "index": 8},
    {"id": "summary", "title": "Summary", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

DASHBOARD_CATEGORIES = (
    "Organizations",
    "Departments",
    "AI Teams",
    "AI Specialists",
    "Concierge",
    "Workflows",
    "Tasks",
    "Documents",
    "Knowledge",
    "Live Sessions",
)

LIVE_STATUSES = (
    "Idle",
    "Working",
    "Thinking",
    "Learning",
    "Analyzing",
    "Collaborating",
    "Waiting",
    "Completed",
    "Offline",
)

ACTIVITY_CHANNELS = (
    "Current Tasks",
    "Running Processes",
    "Knowledge Updates",
    "Workflow Activity",
    "AI Communication",
    "Organization Activity",
)

VISUAL_OBJECT_FIELDS = (
    "logical_id",
    "visual_id",
    "object_type",
    "current_state",
    "logical_state",
    "visual_state",
    "status",
    "relationships",
    "lifecycle",
)

WAIT_STAGES = (
    "Active Specialists",
    "Current Stage",
    "Progress",
    "Knowledge Access",
    "Task Distribution",
    "Decision Building",
    "Expected Completion Stage",
)

HEALTH_SURFACES = (
    "Platform Health",
    "Registry Health",
    "AI Health",
    "Module Health",
    "Performance",
)

AI_CITY_INTERFACES = (
    "Visual Layer",
    "Animated Objects",
    "Future Positioning",
    "Future Movement",
    "Future Live Organization",
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "dashboard_categories": list(DASHBOARD_CATEGORIES),
        "live_statuses": list(LIVE_STATUSES),
        "activity_channels": list(ACTIVITY_CHANNELS),
        "visual_object_fields": list(VISUAL_OBJECT_FIELDS),
        "wait_stages": list(WAIT_STAGES),
        "health_surfaces": list(HEALTH_SURFACES),
        "ai_city_interfaces": list(AI_CITY_INTERFACES),
        "executes_business_logic": False,
        "visualizes_logical_layer": True,
    }
