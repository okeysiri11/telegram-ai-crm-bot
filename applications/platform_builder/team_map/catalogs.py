"""AI Team Map / Live Organization catalogs — Sprint 29.2."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "live_map", "title": "Live Organization Map", "index": 1},
    {"id": "ai_cards", "title": "AI Cards", "index": 2},
    {"id": "live_status", "title": "Live Status", "index": 3},
    {"id": "workload", "title": "Workload Engine", "index": 4},
    {"id": "relationships", "title": "Relationship Map", "index": 5},
    {"id": "live_activity", "title": "Live Activity", "index": 6},
    {"id": "event_bus", "title": "Visual Event Bus", "index": 7},
    {"id": "visual_objects", "title": "Visual Objects", "index": 8},
    {"id": "ai_city_apis", "title": "Foundation for AI City", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

MAP_NODE_TYPES = (
    "Owner",
    "AI Concierge",
    "Departments",
    "AI Teams",
    "AI Specialists",
    "Connections",
    "Organization Hierarchy",
)

AI_CARD_FIELDS = (
    "avatar",
    "name",
    "role",
    "specialization",
    "department",
    "current_status",
    "current_task",
    "current_workload",
    "knowledge_level",
    "health",
)

LIVE_STATUSES = (
    "Idle",
    "Working",
    "Thinking",
    "Learning",
    "Collaborating",
    "Reviewing",
    "Waiting",
    "Offline",
    "Completed",
)

WORKLOAD_METRICS = (
    "Current Load",
    "Task Queue",
    "Response Time",
    "Availability",
    "Utilization",
    "Balanced Work Indicator",
)

RELATIONSHIP_TYPES = (
    "Department Links",
    "AI Collaboration",
    "Knowledge Flow",
    "Workflow Connections",
    "Task Transfers",
    "Organization Structure",
)

ACTIVITY_TYPES = (
    "Current Conversations",
    "Knowledge Updates",
    "Task Assignment",
    "Decision Making",
    "Workflow Progress",
)

EVENT_CHANNELS = (
    "AI Events",
    "Workflow Events",
    "Task Events",
    "Knowledge Events",
    "Organization Events",
    "Registry Events",
)

VISUAL_OBJECT_FIELDS = (
    "logical_id",
    "visual_id",
    "current_position",
    "visual_state",
    "relationship_state",
    "animation_state",
)

AI_CITY_APIS = (
    "Movement API",
    "Animation API",
    "Position API",
    "Visual Object API",
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "map_node_types": list(MAP_NODE_TYPES),
        "ai_card_fields": list(AI_CARD_FIELDS),
        "live_statuses": list(LIVE_STATUSES),
        "workload_metrics": list(WORKLOAD_METRICS),
        "relationship_types": list(RELATIONSHIP_TYPES),
        "activity_types": list(ACTIVITY_TYPES),
        "event_channels": list(EVENT_CHANNELS),
        "visual_object_fields": list(VISUAL_OBJECT_FIELDS),
        "ai_city_apis": list(AI_CITY_APIS),
        "ui": ["Animated Connections", "Interactive Cards", "Zoom", "Pan", "Search", "Filters", "Department Focus"],
    }
