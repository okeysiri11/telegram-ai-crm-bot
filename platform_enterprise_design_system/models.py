"""Design System constants — Sprint 26.2."""

from __future__ import annotations

DESIGN_PATH = "src/web/design-system"
VERSION = "9.0.3"

TOKEN_GROUPS = (
    "colors",
    "fonts",
    "font_sizes",
    "font_weights",
    "border_radius",
    "shadows",
    "spacing",
    "z_index",
    "breakpoints",
    "motion",
    "opacity",
)

COLOR_ROLES = (
    "primary",
    "secondary",
    "success",
    "warning",
    "danger",
    "info",
    "neutral",
    "background",
    "surface",
    "border",
    "text",
    "disabled",
    "hover",
    "active",
    "focus",
)

TYPOGRAPHY_SCALE = (
    "display_xl",
    "display_l",
    "heading_1",
    "heading_2",
    "heading_3",
    "heading_4",
    "body_large",
    "body",
    "small",
    "caption",
    "label",
    "button_text",
)

GRID_VARIANTS = (
    "twelve_column",
    "responsive",
    "fluid_containers",
    "fixed_containers",
    "dashboard",
    "workspace",
)

VIEWPORTS = ("desktop", "laptop", "tablet", "mobile")

ICON_CATEGORIES = (
    "navigation",
    "ai",
    "crm",
    "erp",
    "finance",
    "hr",
    "analytics",
    "notifications",
    "security",
    "settings",
    "workflow",
)

ANIMATIONS = (
    "fade",
    "slide",
    "scale",
    "collapse",
    "expand",
    "page_transition",
    "loading",
    "skeleton",
    "micro_interactions",
)

A11Y_FEATURES = (
    "wcag_aa",
    "keyboard_navigation",
    "screen_reader",
    "focus_management",
    "high_contrast",
    "reduced_motion",
)

CATALOG_COMPONENTS = (
    "buttons",
    "forms",
    "cards",
    "tables",
    "charts",
    "navigation",
    "dialogs",
    "modals",
    "notifications",
    "dashboards",
    "ai_widgets",
    "data_grids",
)

THEMES = ("light", "dark", "corporate", "custom")

DOC_SECTIONS = (
    "component_guide",
    "ui_guidelines",
    "design_tokens_reference",
    "theme_documentation",
    "accessibility_guide",
    "responsive_guide",
)

INTEGRATION_TARGETS = (
    "web_foundation",
    "authentication",
    "dashboard",
    "marketplace",
    "ai_platform",
    "enterprise_hub",
    "notification_center",
)

KPI_TARGETS = {
    "unified_design_system": True,
    "centralized_design_tokens": True,
    "unified_component_library": True,
    "adaptive_grid": True,
    "accessibility_supported": True,
    "centralized_themes": True,
    "full_component_documentation": True,
}

ARCHITECTURE = (
    "design_tokens",
    "color_system",
    "typography",
    "icon_library",
    "grid_system",
    "spacing_system",
    "elevation_system",
    "animation_engine",
    "responsive_engine",
    "accessibility_manager",
    "component_catalog",
    "design_documentation",
)

PRINCIPLES = (
    "tokens_only_no_hardcoded_styles",
    "single_design_system_for_web_platform",
    "wcag_aa_by_default",
    "themeable_branding",
    "no_duplicated_ui_standards",
    "phase3_design_system",
)
