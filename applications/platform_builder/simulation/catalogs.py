"""Visual Simulation Engine catalogs — Sprint 29.7."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "engine", "title": "Simulation Engine", "index": 1},
    {"id": "supported", "title": "Supported Simulations", "index": 2},
    {"id": "live_org", "title": "Live Organization Simulation", "index": 3},
    {"id": "collaboration", "title": "AI Collaboration", "index": 4},
    {"id": "workflow", "title": "Workflow Simulation", "index": 5},
    {"id": "knowledge", "title": "Knowledge Flow", "index": 6},
    {"id": "document", "title": "Document Flow", "index": 7},
    {"id": "timeline", "title": "Simulation Timeline", "index": 8},
    {"id": "performance", "title": "Performance", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

SUPPORTED_SIMULATIONS = (
    "AI Creation",
    "AI Initialization",
    "AI Activation",
    "AI Shutdown",
    "AI Recovery",
    "Department Creation",
    "Department Merge",
    "Department Split",
    "Organization Creation",
    "Workspace Creation",
    "Workflow Launch",
    "Workflow Completion",
    "Task Assignment",
    "Task Transfer",
    "Task Completion",
    "Knowledge Synchronization",
    "Knowledge Distribution",
    "Knowledge Update",
    "Document Creation",
    "Document Review",
    "Document Approval",
    "Document Archive",
)

# Map simulation names → Visual Event Bus channel + event_type
SIMULATION_EVENT_MAP = {
    "AI Creation": ("AI Events", "ai_creation"),
    "AI Initialization": ("AI Events", "ai_initialization"),
    "AI Activation": ("AI Events", "ai_activation"),
    "AI Shutdown": ("AI Events", "ai_shutdown"),
    "AI Recovery": ("AI Events", "ai_recovery"),
    "Department Creation": ("Organization Events", "department_creation"),
    "Department Merge": ("Organization Events", "department_merge"),
    "Department Split": ("Organization Events", "department_split"),
    "Organization Creation": ("Organization Events", "organization_creation"),
    "Workspace Creation": ("Organization Events", "workspace_creation"),
    "Workflow Launch": ("Workflow Events", "workflow_launch"),
    "Workflow Completion": ("Workflow Events", "workflow_completion"),
    "Task Assignment": ("Task Events", "task_assignment"),
    "Task Transfer": ("Task Events", "task_transfer"),
    "Task Completion": ("Task Events", "task_completion"),
    "Knowledge Synchronization": ("Knowledge Events", "knowledge_synchronization"),
    "Knowledge Distribution": ("Knowledge Events", "knowledge_distribution"),
    "Knowledge Update": ("Knowledge Events", "knowledge_update"),
    "Document Creation": ("Knowledge Events", "document_creation"),
    "Document Review": ("Knowledge Events", "document_review"),
    "Document Approval": ("Knowledge Events", "document_approval"),
    "Document Archive": ("Knowledge Events", "document_archive"),
}

LIVE_ORG_SURFACES = (
    "Department Expansion",
    "Team Growth",
    "New Specialists",
    "Organization Restructure",
    "Hierarchy Changes",
)

COLLABORATION_VISUALS = (
    "Conversation",
    "Delegation",
    "Cooperation",
    "Knowledge Sharing",
    "Collective Decision",
    "Parallel Execution",
    "Supervisor Review",
)

WORKFLOW_STAGES = (
    "Workflow Start",
    "Current Stage",
    "Branch Selection",
    "Approval Flow",
    "Execution Progress",
    "Completion",
)

KNOWLEDGE_FLOW = (
    "Knowledge Creation",
    "Knowledge Validation",
    "Knowledge Publishing",
    "Knowledge Consumption",
    "Knowledge Evolution",
)

DOCUMENT_FLOW = (
    "Draft",
    "Review",
    "Approval",
    "Distribution",
    "Archive",
)

TIMELINE_CONTROLS = (
    "Pause",
    "Resume",
    "Speed Control",
    "Step Forward",
    "Replay Buffer Interface",
)

PERF_FEATURES = (
    "Simulation Pool",
    "Frame Optimization",
    "Object Reuse",
    "Adaptive Detail",
    "Viewport Simulation",
)

UI_SURFACES = (
    "Live Timeline",
    "Simulation Status",
    "Active Simulation Counter",
    "Current Simulation Queue",
    "Organization Activity Feed",
)


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "supported_simulations": list(SUPPORTED_SIMULATIONS),
        "live_org_surfaces": list(LIVE_ORG_SURFACES),
        "collaboration_visuals": list(COLLABORATION_VISUALS),
        "workflow_stages": list(WORKFLOW_STAGES),
        "knowledge_flow": list(KNOWLEDGE_FLOW),
        "document_flow": list(DOCUMENT_FLOW),
        "timeline_controls": list(TIMELINE_CONTROLS),
        "performance_features": list(PERF_FEATURES),
        "ui_surfaces": list(UI_SURFACES),
        "creates_fake_events": False,
        "originates_from_visual_event_bus": True,
        "enterprise_design_system": True,
        "dark_mode": True,
        "responsive": True,
        "gpu_optimized": True,
        "visual_layer": True,
        "visual_event_bus": True,
        "visual_behavior_engine": True,
        "visual_rendering_engine": True,
    }
