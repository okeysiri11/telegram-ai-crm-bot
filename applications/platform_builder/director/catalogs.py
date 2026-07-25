"""Visual Director Engine catalogs — Sprint 29.8."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "director", "title": "Director Engine", "index": 1},
    {"id": "scenes", "title": "Scene Management", "index": 2},
    {"id": "focus", "title": "Focus Engine", "index": 3},
    {"id": "attention", "title": "Attention Management", "index": 4},
    {"id": "coordination", "title": "Simulation Coordination", "index": 5},
    {"id": "live_org", "title": "Live Organization", "index": 6},
    {"id": "camera", "title": "Intelligent Camera API", "index": 7},
    {"id": "conflicts", "title": "Conflict Resolution", "index": 8},
    {"id": "performance", "title": "Performance", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

DIRECTOR_COMPONENTS = (
    "Director Engine",
    "Scene Director",
    "Focus Manager",
    "Attention Manager",
    "Priority Manager",
)

SCENE_FEATURES = (
    "Scene Creation",
    "Scene Switching",
    "Scene Synchronization",
    "Scene Lifecycle",
    "Scene State",
)

FOCUS_TARGETS = (
    "Highest Priority AI",
    "Most Active Department",
    "Critical Workflow",
    "Urgent Notification",
    "Current Decision Point",
    "Organization Highlights",
)

ATTENTION_COORDINATION = (
    "Visual Focus",
    "Camera Focus",
    "Object Highlighting",
    "Animation Priority",
    "Notification Timing",
)

COORDINATED_ENGINES = (
    "Behavior Engine",
    "Simulation Engine",
    "Rendering Engine",
    "Theme Engine",
    "LOD Engine",
)

LIVE_ORG_DIRECTIVES = (
    "AI Collaboration",
    "Knowledge Flow",
    "Workflow Progress",
    "Department Activity",
    "Executive Overview",
)

CAMERA_API = (
    "Camera Position",
    "Camera Tracking",
    "Smooth Follow",
    "Zoom Targets",
    "Focus Targets",
    "Future AI City Navigation",
)

CONFLICT_PREVENTIONS = (
    "Animation Collisions",
    "Focus Conflicts",
    "Notification Flooding",
    "Visual Overlap",
    "Priority Conflicts",
)

PERF_FEATURES = (
    "Adaptive Rendering",
    "Priority Scheduling",
    "Viewport Awareness",
    "Resource Coordination",
)

UI_SURFACES = (
    "Live Focus Indicator",
    "Scene Status",
    "Attention Queue",
    "Current Highlight",
    "Priority Timeline",
)

SCENE_LIFECYCLE = ("created", "active", "paused", "synchronized", "archived")


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "director_components": list(DIRECTOR_COMPONENTS),
        "scene_features": list(SCENE_FEATURES),
        "focus_targets": list(FOCUS_TARGETS),
        "attention_coordination": list(ATTENTION_COORDINATION),
        "coordinated_engines": list(COORDINATED_ENGINES),
        "live_org_directives": list(LIVE_ORG_DIRECTIVES),
        "camera_api": list(CAMERA_API),
        "conflict_preventions": list(CONFLICT_PREVENTIONS),
        "performance_features": list(PERF_FEATURES),
        "ui_surfaces": list(UI_SURFACES),
        "scene_lifecycle": list(SCENE_LIFECYCLE),
        "generates_business_events": False,
        "orchestrates_visual_presentation_only": True,
        "enterprise_design_system": True,
        "dark_mode": True,
        "responsive": True,
        "gpu_optimized": True,
        "visual_layer": True,
    }
