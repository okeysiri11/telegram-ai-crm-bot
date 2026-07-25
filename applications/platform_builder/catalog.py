"""Builder catalog and framework definitions — Sprint 28.1."""

from __future__ import annotations

from typing import Any

FRAMEWORK_PHASES = (
    "step",
    "explanation",
    "information",
    "example",
    "preview",
    "create",
)

AI_BUILDER_STEPS = (
    "Number of AI Agents",
    "AI Agent Name",
    "Profession",
    "Specialization",
    "Knowledge",
    "Skills",
    "Permissions",
    "Personality",
    "Summary",
    "Create",
)

CONCIERGE_STEPS = (
    "Concierge Identity",
    "Concierge Role",
    "Organization Access",
    "AI Orchestration",
    "Proactive Assistance",
    "Owner Relationship",
    "Smart Recommendations",
    "Summary",
    "Create",
)

GENERIC_STEPS = (
    "Define Scope",
    "Configure Structure",
    "Set Options",
    "Review Information",
    "Preview",
    "Create",
)

BUILDERS: list[dict[str, Any]] = [
    {
        "id": "dashboard",
        "name": "Dashboard",
        "route": "/platform-builder",
        "kind": "hub",
        "status": "operational",
        "learning_supported": True,
        "frame_only": False,
    },
    {
        "id": "vertical",
        "name": "Vertical Builder",
        "route": "/platform-builder/vertical",
        "kind": "builder",
        "status": "frame",
        "learning_supported": True,
        "frame_only": True,
        "steps": list(GENERIC_STEPS),
        "purpose": "Prepare industry vertical blueprints for future activation.",
    },
    {
        "id": "ai",
        "name": "AI Builder",
        "route": "/platform-builder/ai",
        "kind": "builder",
        "status": "operational",
        "learning_supported": True,
        "frame_only": False,
        "steps": list(AI_BUILDER_STEPS),
        "purpose": "Compose AI agent teams with clear roles and personalities.",
    },
    {
        "id": "concierge",
        "name": "Concierge Builder",
        "route": "/platform-builder/concierge",
        "kind": "builder",
        "status": "operational",
        "learning_supported": True,
        "frame_only": False,
        "steps": list(CONCIERGE_STEPS),
        "purpose": "Configure the single organizational Concierge assistant.",
        "constraints": {"one_per_organization": True, "separate_from_ai_agents": True},
    },
    {
        "id": "crm",
        "name": "CRM Builder",
        "route": "/platform-builder/crm",
        "kind": "builder",
        "status": "frame",
        "learning_supported": True,
        "frame_only": True,
        "steps": list(GENERIC_STEPS),
    },
    {
        "id": "erp",
        "name": "ERP Builder",
        "route": "/platform-builder/erp",
        "kind": "builder",
        "status": "frame",
        "learning_supported": True,
        "frame_only": True,
        "steps": list(GENERIC_STEPS),
    },
    {
        "id": "workflow",
        "name": "Workflow Builder",
        "route": "/platform-builder/workflow",
        "kind": "builder",
        "status": "frame",
        "learning_supported": True,
        "frame_only": True,
        "steps": list(GENERIC_STEPS),
    },
    {
        "id": "knowledge",
        "name": "Knowledge Builder",
        "route": "/platform-builder/knowledge",
        "kind": "builder",
        "status": "frame",
        "learning_supported": True,
        "frame_only": True,
        "steps": list(GENERIC_STEPS),
    },
    {
        "id": "automation",
        "name": "Automation Builder",
        "route": "/platform-builder/automation",
        "kind": "builder",
        "status": "frame",
        "learning_supported": True,
        "frame_only": True,
        "steps": list(GENERIC_STEPS),
    },
    {
        "id": "dashboard_builder",
        "name": "Dashboard Builder",
        "route": "/platform-builder/dashboard-builder",
        "kind": "builder",
        "status": "frame",
        "learning_supported": True,
        "frame_only": True,
        "steps": list(GENERIC_STEPS),
    },
    {
        "id": "template",
        "name": "Template Builder",
        "route": "/platform-builder/template",
        "kind": "builder",
        "status": "frame",
        "learning_supported": True,
        "frame_only": True,
        "steps": list(GENERIC_STEPS),
    },
    {
        "id": "marketplace",
        "name": "Marketplace Builder",
        "route": "/platform-builder/marketplace",
        "kind": "builder",
        "status": "frame",
        "learning_supported": True,
        "frame_only": True,
        "steps": list(GENERIC_STEPS),
    },
    {
        "id": "academy",
        "name": "Builder Academy",
        "route": "/platform-builder/academy",
        "kind": "academy",
        "status": "operational",
        "learning_supported": True,
        "frame_only": False,
    },
    {
        "id": "god_mode",
        "name": "God Mode",
        "route": "/platform-builder/god-mode",
        "kind": "god_mode",
        "status": "operational",
        "learning_supported": False,
        "frame_only": False,
        "requires_role": "platform_owner",
        "visibility": "platform_owner_only",
    },
]


def get_builder(builder_id: str) -> dict[str, Any] | None:
    return next((b for b in BUILDERS if b["id"] == builder_id), None)


def menu_for_role(role: str | None = None) -> list[dict[str, Any]]:
    items = []
    for b in BUILDERS:
        if b.get("requires_role") == "platform_owner" and role != "platform_owner":
            continue
        items.append(
            {
                "id": b["id"],
                "name": b["name"],
                "route": b["route"],
                "kind": b["kind"],
                "status": b["status"],
            }
        )
    return items
