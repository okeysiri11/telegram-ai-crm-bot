"""Visual Rendering Engine catalogs — Sprint 29.4."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "renderer", "title": "Visual Renderer", "index": 1},
    {"id": "lod", "title": "Visual LOD Engine", "index": 2},
    {"id": "viewport", "title": "Smart Viewport", "index": 3},
    {"id": "layers", "title": "Layer System", "index": 4},
    {"id": "priority", "title": "Object Priority", "index": 5},
    {"id": "animation_opt", "title": "Animation Optimization", "index": 6},
    {"id": "live_org", "title": "Live Organization Support", "index": 7},
    {"id": "ai_city", "title": "Foundation for AI City", "index": 8},
    {"id": "performance", "title": "Performance", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

RENDERER_CAPABILITIES = (
    "Render Queue",
    "Object Pool",
    "Layer Rendering",
    "Viewport Rendering",
    "Animation Rendering",
)

LOD_LEVELS = (
    {"id": "L0", "label": "Organizations", "min_zoom": 0.0, "max_zoom": 0.35},
    {"id": "L1", "label": "Departments", "min_zoom": 0.35, "max_zoom": 0.55},
    {"id": "L2", "label": "AI Teams", "min_zoom": 0.55, "max_zoom": 0.75},
    {"id": "L3", "label": "AI Specialists", "min_zoom": 0.75, "max_zoom": 0.9},
    {
        "id": "L4",
        "label": "Documents · Tasks · Connections · Animations",
        "min_zoom": 0.9,
        "max_zoom": 2.0,
    },
)

LOD_OBJECT_TYPES = {
    "L0": ("organization",),
    "L1": ("organization", "department"),
    "L2": ("organization", "department", "ai_team"),
    "L3": ("organization", "department", "ai_team", "ai_specialist", "concierge"),
    "L4": (
        "organization",
        "department",
        "ai_team",
        "ai_specialist",
        "concierge",
        "document",
        "task",
        "connection",
        "animation",
        "knowledge",
        "workflow",
    ),
}

RENDER_LAYERS = (
    "Background",
    "Buildings",
    "Departments",
    "AI",
    "Documents",
    "Connections",
    "Effects",
    "Notifications",
)

PRIORITY_BANDS = {
    "high": ("Visible AI", "Running Tasks", "Live Conversations"),
    "medium": ("Documents", "Knowledge", "Workflow"),
    "low": ("Archived Objects", "Completed Tasks"),
}

ANIMATION_OPT = (
    "Animation Pool",
    "Frame Limiter",
    "Smooth Transitions",
    "Adaptive Animation Quality",
)

LIVE_ORG_SURFACES = (
    "Current Activity",
    "AI Status",
    "Department Status",
    "Task Flow",
    "Knowledge Flow",
    "Workflow State",
)

AI_CITY_RENDER = (
    "Tile Rendering",
    "Future Map Rendering",
    "Future Character Rendering",
    "Future Building Rendering",
)

PERF_METRICS = (
    "FPS Monitor",
    "Memory Monitor",
    "Object Count",
    "Render Time",
    "GPU Statistics",
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "renderer_capabilities": list(RENDERER_CAPABILITIES),
        "lod_levels": [dict(l) for l in LOD_LEVELS],
        "render_layers": list(RENDER_LAYERS),
        "priority_bands": {k: list(v) for k, v in PRIORITY_BANDS.items()},
        "animation_optimization": list(ANIMATION_OPT),
        "live_org_surfaces": list(LIVE_ORG_SURFACES),
        "ai_city_render": list(AI_CITY_RENDER),
        "performance_metrics": list(PERF_METRICS),
        "executes_business_logic": False,
        "independent_from_business_logic": True,
        "updates_from": ["Visual Event Bus", "Visual Behavior Engine"],
        "gpu_friendly": True,
    }
