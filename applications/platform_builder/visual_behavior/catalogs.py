"""Visual Behavior Engine catalogs — Sprint 29.3."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "behavior_engine", "title": "Visual Behavior Engine", "index": 1},
    {"id": "behaviors", "title": "Supported Behaviors", "index": 2},
    {"id": "transitions", "title": "Transition Engine", "index": 3},
    {"id": "animation_framework", "title": "Animation Framework", "index": 4},
    {"id": "object_types", "title": "Object Types", "index": 5},
    {"id": "event_subscriptions", "title": "Event Subscriptions", "index": 6},
    {"id": "wait_experience", "title": "Wait Experience", "index": 7},
    {"id": "performance", "title": "Performance", "index": 8},
    {"id": "ai_city_foundation", "title": "Foundation for AI City", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

BEHAVIORS = (
    "Idle",
    "Working",
    "Thinking",
    "Learning",
    "Searching",
    "Analyzing",
    "Collaborating",
    "Reviewing",
    "Waiting",
    "Completed",
    "Offline",
)

TRANSITIONS = (
    ("Idle", "Working"),
    ("Working", "Thinking"),
    ("Thinking", "Collaborating"),
    ("Collaborating", "Completed"),
    ("Completed", "Idle"),
)

ANIMATIONS = (
    "Pulse",
    "Glow",
    "Movement",
    "Connection Animation",
    "Progress Animation",
    "Knowledge Animation",
    "Task Animation",
)

OBJECT_TYPES = (
    "AI Specialists",
    "Concierge",
    "Departments",
    "Documents",
    "Tasks",
    "Workflows",
    "Knowledge",
    "Organizations",
)

OBJECT_TYPE_KEYS = (
    "ai_specialist",
    "concierge",
    "department",
    "document",
    "task",
    "workflow",
    "knowledge",
    "organization",
)

PERFORMANCE_FEATURES = (
    "Animation Pool",
    "Object Reuse",
    "Frame Optimization",
    "Lazy Rendering",
    "Viewport Rendering",
)

AI_CITY_APIS = (
    "Movement API",
    "Behavior API",
    "Animation API",
    "Visual State API",
)

STATE_FIELDS = (
    "visual_state",
    "behavior_state",
    "animation_state",
    "transition_state",
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "behaviors": list(BEHAVIORS),
        "transitions": [{"from": a, "to": b} for a, b in TRANSITIONS],
        "animations": list(ANIMATIONS),
        "object_types": list(OBJECT_TYPES),
        "object_type_keys": list(OBJECT_TYPE_KEYS),
        "performance_features": list(PERFORMANCE_FEATURES),
        "ai_city_apis": list(AI_CITY_APIS),
        "state_fields": list(STATE_FIELDS),
        "executes_business_logic": False,
        "reacts_to_visual_event_bus_only": True,
    }
