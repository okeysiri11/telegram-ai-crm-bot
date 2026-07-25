"""Visual Story Engine catalogs — Sprint 29.9."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "engine", "title": "Story Engine", "index": 1},
    {"id": "types", "title": "Story Types", "index": 2},
    {"id": "segments", "title": "Story Segments", "index": 3},
    {"id": "org_evolution", "title": "Organization Evolution", "index": 4},
    {"id": "ai_stories", "title": "AI Stories", "index": 5},
    {"id": "workflow_stories", "title": "Workflow Stories", "index": 6},
    {"id": "knowledge_stories", "title": "Knowledge Stories", "index": 7},
    {"id": "executive", "title": "Executive Mode", "index": 8},
    {"id": "navigation", "title": "Story Navigation", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

STORY_ENGINE_COMPONENTS = (
    "Story Engine",
    "Story Registry",
    "Story Builder",
    "Story Timeline",
    "Story Controller",
)

STORY_TYPES = (
    "Organization Story",
    "Department Story",
    "AI Agent Story",
    "Workflow Story",
    "Knowledge Story",
    "Document Story",
    "Project Story",
    "Executive Story",
)

STORY_SEGMENTS = (
    "Beginning",
    "Initialization",
    "Growth",
    "Collaboration",
    "Decision",
    "Execution",
    "Completion",
    "Archive",
)

ORG_EVOLUTION = (
    "Organization Creation",
    "Department Expansion",
    "Team Growth",
    "Hiring AI Specialists",
    "Restructuring",
    "Executive Changes",
)

AI_STORY_BEATS = (
    "Agent Creation",
    "Training",
    "Knowledge Acquisition",
    "Task Execution",
    "Collaboration",
    "Promotion",
    "Retirement",
)

WORKFLOW_STORY_BEATS = (
    "Workflow Start",
    "Execution Path",
    "Approval Chain",
    "Parallel Branches",
    "Completion",
    "Business Result",
)

KNOWLEDGE_STORY_BEATS = (
    "Knowledge Creation",
    "Validation",
    "Distribution",
    "Usage",
    "Improvement",
)

EXECUTIVE_SUMMARIES = (
    "Today's Progress",
    "Weekly Activity",
    "Project Evolution",
    "Organization Development",
    "Major Milestones",
)

NAVIGATION_CONTROLS = (
    "Play",
    "Pause",
    "Step",
    "Timeline Navigation",
    "Bookmarks",
    "Milestones",
)

UI_SURFACES = (
    "Story Timeline",
    "Story Player",
    "Milestone Viewer",
    "Executive Summary",
    "Story History",
)

# Map story types → Visual Event Bus channels (grouping only)
STORY_CHANNEL_MAP = {
    "Organization Story": ("Organization Events",),
    "Department Story": ("Organization Events",),
    "AI Agent Story": ("AI Events",),
    "Workflow Story": ("Workflow Events", "Task Events"),
    "Knowledge Story": ("Knowledge Events",),
    "Document Story": ("Knowledge Events",),
    "Project Story": ("Workflow Events", "Task Events", "Organization Events"),
    "Executive Story": (
        "AI Events",
        "Workflow Events",
        "Task Events",
        "Knowledge Events",
        "Organization Events",
        "Registry Events",
    ),
}

# Heuristic segment assignment from event_type keywords (presentation grouping only)
SEGMENT_KEYWORDS = {
    "Beginning": ("creation", "created", "start", "launch"),
    "Initialization": ("initialization", "init", "bootstrap", "registered"),
    "Growth": ("growth", "expansion", "hiring", "merge"),
    "Collaboration": ("collaborat", "sharing", "delegation", "cooperation"),
    "Decision": ("decision", "approval", "review", "branch"),
    "Execution": ("execution", "activation", "working", "progress", "assignment"),
    "Completion": ("completion", "completed", "done", "result"),
    "Archive": ("archive", "shutdown", "retirement", "offline"),
}


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "components": list(STORY_ENGINE_COMPONENTS),
        "story_types": list(STORY_TYPES),
        "story_segments": list(STORY_SEGMENTS),
        "organization_evolution": list(ORG_EVOLUTION),
        "ai_story_beats": list(AI_STORY_BEATS),
        "workflow_story_beats": list(WORKFLOW_STORY_BEATS),
        "knowledge_story_beats": list(KNOWLEDGE_STORY_BEATS),
        "executive_summaries": list(EXECUTIVE_SUMMARIES),
        "navigation_controls": list(NAVIGATION_CONTROLS),
        "ui_surfaces": list(UI_SURFACES),
        "creates_business_events": False,
        "modifies_business_events": False,
        "reorders_business_events": False,
        "groups_verified_bus_events_only": True,
        "enterprise_design_system": True,
        "dark_mode": True,
        "responsive": True,
        "gpu_optimized": True,
        "visual_layer": True,
        "visual_event_bus": True,
    }
