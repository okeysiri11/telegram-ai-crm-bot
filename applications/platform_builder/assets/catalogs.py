"""Visual Asset Registry catalogs — Sprint 29.6."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "registry", "title": "Visual Asset Registry", "index": 1},
    {"id": "categories", "title": "Asset Categories", "index": 2},
    {"id": "versions", "title": "Version Management", "index": 3},
    {"id": "optimization", "title": "Resource Optimization", "index": 4},
    {"id": "avatars", "title": "AI Avatar Library", "index": 5},
    {"id": "branding", "title": "Organization Branding", "index": 6},
    {"id": "ai_city", "title": "Foundation for AI City", "index": 7},
    {"id": "search", "title": "Search", "index": 8},
    {"id": "performance", "title": "Performance", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

ASSET_TYPES = (
    "Images",
    "Icons",
    "Avatars",
    "Illustrations",
    "Animations",
    "Effects",
    "Themes",
    "Future AI City Assets",
)

ASSET_CATEGORIES = (
    "AI",
    "Departments",
    "Organizations",
    "Buildings",
    "Documents",
    "Tasks",
    "Knowledge",
    "Workflow",
    "Marketplace",
    "UI Components",
)

VERSION_FEATURES = (
    "Asset Version",
    "Revision History",
    "Replace Asset",
    "Rollback Asset",
    "Compatibility Check",
)

OPTIMIZATION_FEATURES = (
    "Lazy Loading",
    "Caching",
    "Compression",
    "Resource Pool",
    "Duplicate Detection",
)

AVATAR_LIBRARY = (
    "Base Characters",
    "Portraits",
    "Expressions",
    "Accessories",
    "Role Decorations",
    "Department Decorations",
    "Achievement Decorations",
    "Future Character Equipment",
)

ORG_BRANDING_ASSETS = (
    "Logos",
    "Brand Assets",
    "Corporate Icons",
    "Theme Resources",
    "Department Resources",
)

AI_CITY_ASSETS = (
    "Buildings",
    "Roads",
    "Environment Objects",
    "Character Sprites",
    "Animated Objects",
    "Effects",
)

SEARCH_FACETS = (
    "Category",
    "Organization",
    "Department",
    "Type",
    "Theme",
    "Tags",
)

PERF_METRICS = (
    "Memory Usage",
    "Cache Size",
    "Asset Count",
    "Optimization Status",
)

SEED_ASSETS = (
    {
        "asset_id": "asset_ai_avatar_base",
        "name": "AI Base Character",
        "asset_type": "Avatars",
        "category": "AI",
        "organization_id": "org_default",
        "department_id": "dept_ops",
        "theme_id": "enterprise_dark",
        "tags": ["avatar", "base", "ai"],
        "uri": "/assets/ai/avatar_base.svg",
        "version": "1.0.0",
        "checksum": "sha256:avatar_base_v1",
        "size_kb": 24,
    },
    {
        "asset_id": "asset_org_logo",
        "name": "Organization Logo",
        "asset_type": "Images",
        "category": "Organizations",
        "organization_id": "org_default",
        "department_id": None,
        "theme_id": "enterprise_dark",
        "tags": ["logo", "brand"],
        "uri": "/assets/org/logo.svg",
        "version": "1.0.0",
        "checksum": "sha256:org_logo_v1",
        "size_kb": 12,
    },
    {
        "asset_id": "asset_dept_icon",
        "name": "Department Icon",
        "asset_type": "Icons",
        "category": "Departments",
        "organization_id": "org_default",
        "department_id": "dept_ops",
        "theme_id": "enterprise_light",
        "tags": ["icon", "department"],
        "uri": "/assets/dept/ops.svg",
        "version": "1.0.0",
        "checksum": "sha256:dept_ops_v1",
        "size_kb": 4,
    },
    {
        "asset_id": "asset_doc_illust",
        "name": "Document Illustration",
        "asset_type": "Illustrations",
        "category": "Documents",
        "organization_id": "org_default",
        "department_id": "dept_knowledge",
        "theme_id": "enterprise_dark",
        "tags": ["document", "illustration"],
        "uri": "/assets/docs/doc.svg",
        "version": "1.0.0",
        "checksum": "sha256:doc_illust_v1",
        "size_kb": 36,
    },
    {
        "asset_id": "asset_fx_pulse",
        "name": "Pulse Effect",
        "asset_type": "Effects",
        "category": "UI Components",
        "organization_id": None,
        "department_id": None,
        "theme_id": "enterprise_dark",
        "tags": ["effect", "pulse", "ui"],
        "uri": "/assets/fx/pulse.json",
        "version": "1.0.0",
        "checksum": "sha256:fx_pulse_v1",
        "size_kb": 8,
    },
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "asset_types": list(ASSET_TYPES),
        "categories": list(ASSET_CATEGORIES),
        "version_features": list(VERSION_FEATURES),
        "optimization_features": list(OPTIMIZATION_FEATURES),
        "avatar_library": list(AVATAR_LIBRARY),
        "org_branding_assets": list(ORG_BRANDING_ASSETS),
        "ai_city_assets": list(AI_CITY_ASSETS),
        "search_facets": list(SEARCH_FACETS),
        "performance_metrics": list(PERF_METRICS),
        "contains_business_logic": False,
        "separated_from_business_logic": True,
        "enterprise_design_system": True,
        "dark_mode": True,
        "responsive": True,
        "high_performance": True,
        "visual_layer": True,
    }
