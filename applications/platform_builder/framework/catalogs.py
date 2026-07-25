"""Universal Builder Framework catalogs — Sprint 28.5."""

from __future__ import annotations

from typing import Any


LIFECYCLE = (
    "initialize",
    "configure",
    "validate",
    "preview",
    "summary",
    "create",
    "register",
    "finish",
)

WIZARD_STEPS = [
    {"id": "template", "title": "Universal Builder Template", "index": 1},
    {"id": "ui_components", "title": "Universal UI Components", "index": 2},
    {"id": "validation", "title": "Validation Framework", "index": 3},
    {"id": "live_preview", "title": "Live Preview Engine", "index": 4},
    {"id": "builder_registry", "title": "Builder Registry", "index": 5},
    {"id": "template_engine", "title": "Template Engine", "index": 6},
    {"id": "extensions", "title": "Extension System", "index": 7},
    {"id": "sdk", "title": "Builder SDK", "index": 8},
    {"id": "summary", "title": "Summary", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

UI_COMPONENTS = (
    "Wizard",
    "Cards",
    "Forms",
    "Progress Bar",
    "Stepper",
    "Preview Window",
    "Summary Screen",
    "Confirmation Screen",
    "Live Validation",
    "Animations",
)

VALIDATION_RULES = (
    {"id": "required_fields", "name": "Required Fields"},
    {"id": "duplicate_detection", "name": "Duplicate Detection"},
    {"id": "registry_validation", "name": "Registry Validation"},
    {"id": "dependency_validation", "name": "Dependency Validation"},
    {"id": "knowledge_validation", "name": "Knowledge Validation"},
    {"id": "relationship_validation", "name": "Relationship Validation"},
    {"id": "live_error_detection", "name": "Live Error Detection"},
    {"id": "suggestion_engine", "name": "Suggestion Engine"},
)

PREVIEW_CAPABILITIES = (
    "Instant Preview",
    "Live Update",
    "Realtime Validation",
    "Visual Summary",
)

TARGET_BUILDERS = (
    {"id": "ai", "name": "AI Builder", "status": "operational"},
    {"id": "concierge", "name": "Concierge Builder", "status": "operational"},
    {"id": "vertical", "name": "Vertical Builder", "status": "operational"},
    {"id": "workflow", "name": "Workflow Builder", "status": "frame"},
    {"id": "crm", "name": "CRM Builder", "status": "frame"},
    {"id": "erp", "name": "ERP Builder", "status": "frame"},
    {"id": "knowledge", "name": "Knowledge Builder", "status": "frame"},
    {"id": "marketplace", "name": "Marketplace Builder", "status": "frame"},
    {"id": "dashboard_builder", "name": "Dashboard Builder", "status": "frame"},
    {"id": "automation", "name": "Automation Builder", "status": "frame"},
    {"id": "document", "name": "Document Builder", "status": "planned"},
    {"id": "department", "name": "Department Builder", "status": "planned"},
    {"id": "user", "name": "User Builder", "status": "planned"},
    {"id": "future", "name": "Future Builders", "status": "extensible"},
)

EXTENSION_TYPES = (
    "Plugins",
    "Custom Steps",
    "Custom Validation",
    "Custom Components",
    "Future Marketplace Extensions",
)

SDK_APIS_PLANNED = (
    "define_builder(schema)",
    "register_steps(builder_id, steps)",
    "attach_validation(builder_id, rules)",
    "attach_components(builder_id, components)",
    "save_template(builder_id, config)",
    "clone_builder(builder_id)",
    "run_lifecycle(session_id)",
)


def full_catalog() -> dict[str, Any]:
    return {
        "lifecycle": list(LIFECYCLE),
        "steps": WIZARD_STEPS,
        "ui_components": list(UI_COMPONENTS),
        "validation_rules": list(VALIDATION_RULES),
        "preview_capabilities": list(PREVIEW_CAPABILITIES),
        "target_builders": list(TARGET_BUILDERS),
        "extension_types": list(EXTENSION_TYPES),
        "sdk_apis_planned": list(SDK_APIS_PLANNED),
        "architecture": {
            "one_common_pipeline": True,
            "reusable_components": True,
            "minimal_effort_for_future_builders": True,
        },
    }
