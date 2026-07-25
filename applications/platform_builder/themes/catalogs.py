"""Visual Theme Engine catalogs — Sprint 29.5."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "theme_engine", "title": "Theme Engine", "index": 1},
    {"id": "color_system", "title": "Color System", "index": 2},
    {"id": "branding", "title": "Enterprise Branding", "index": 3},
    {"id": "components", "title": "Component Theming", "index": 4},
    {"id": "ai_style", "title": "AI Visual Style", "index": 5},
    {"id": "animation_themes", "title": "Animation Themes", "index": 6},
    {"id": "accessibility", "title": "Accessibility", "index": 7},
    {"id": "live_switching", "title": "Live Theme Switching", "index": 8},
    {"id": "ai_city", "title": "Foundation for AI City", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

THEME_SCOPES = (
    "Global Themes",
    "Organization Themes",
    "Department Themes",
    "Workspace Themes",
    "Future AI City Themes",
)

COLOR_TOKENS = (
    "Primary",
    "Secondary",
    "Accent",
    "Background",
    "Surface",
    "Status Colors",
    "Gradient Presets",
)

BRANDING_FIELDS = (
    "Logo",
    "Brand Colors",
    "Typography",
    "Icons",
    "Dashboard Style",
)

COMPONENT_TARGETS = (
    "Cards",
    "Buttons",
    "Navigation",
    "Forms",
    "Dashboards",
    "Dialogs",
    "Tables",
    "Widgets",
)

AI_VISUAL_STYLES = (
    "Avatar Frames",
    "Role Colors",
    "Department Colors",
    "Status Indicators",
    "Achievement Badges",
    "Future Character Styles",
)

ANIMATION_THEME_KEYS = (
    "Animation Speed",
    "Transition Style",
    "Glow Effects",
    "Connection Effects",
    "Notification Effects",
)

ACCESSIBILITY_FEATURES = (
    "High Contrast",
    "Large Fonts",
    "Reduced Motion",
    "Color Safe Palette",
)

AI_CITY_THEME_FOUNDATION = (
    "Building Themes",
    "Environment Themes",
    "Season Themes",
    "Organization Identity",
)

DEFAULT_PALETTES = {
    "dark": {
        "Primary": "#3B82F6",
        "Secondary": "#64748B",
        "Accent": "#22D3EE",
        "Background": "#0B1220",
        "Surface": "#111827",
        "Status Colors": {"ok": "#22C55E", "warn": "#F59E0B", "error": "#EF4444", "info": "#38BDF8"},
        "Gradient Presets": ["#0B1220→#1E293B", "#1E3A8A→#0EA5E9"],
    },
    "light": {
        "Primary": "#2563EB",
        "Secondary": "#64748B",
        "Accent": "#0891B2",
        "Background": "#F8FAFC",
        "Surface": "#FFFFFF",
        "Status Colors": {"ok": "#16A34A", "warn": "#D97706", "error": "#DC2626", "info": "#0284C7"},
        "Gradient Presets": ["#F8FAFC→#E2E8F0", "#DBEAFE→#E0F2FE"],
    },
}

BUILTIN_THEMES = (
    {
        "theme_id": "enterprise_dark",
        "name": "Enterprise Dark",
        "mode": "dark",
        "scope": "Global Themes",
        "builtin": True,
    },
    {
        "theme_id": "enterprise_light",
        "name": "Enterprise Light",
        "mode": "light",
        "scope": "Global Themes",
        "builtin": True,
    },
    {
        "theme_id": "org_default",
        "name": "Organization Default",
        "mode": "dark",
        "scope": "Organization Themes",
        "builtin": True,
    },
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "theme_scopes": list(THEME_SCOPES),
        "color_tokens": list(COLOR_TOKENS),
        "branding_fields": list(BRANDING_FIELDS),
        "component_targets": list(COMPONENT_TARGETS),
        "ai_visual_styles": list(AI_VISUAL_STYLES),
        "animation_theme_keys": list(ANIMATION_THEME_KEYS),
        "accessibility_features": list(ACCESSIBILITY_FEATURES),
        "ai_city_theme_foundation": list(AI_CITY_THEME_FOUNDATION),
        "builtin_themes": [dict(t) for t in BUILTIN_THEMES],
        "modes": ["dark", "light"],
        "contains_business_logic": False,
        "affects_appearance_only": True,
        "enterprise_design_system": True,
        "responsive": True,
        "high_performance": True,
        "visual_layer": True,
    }
