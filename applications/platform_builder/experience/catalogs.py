"""Visual Experience Engine catalogs — Sprint 29.11."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "engine", "title": "Visual Experience Engine", "index": 1},
    {"id": "unified", "title": "Unified Experience", "index": 2},
    {"id": "context", "title": "User Context", "index": 3},
    {"id": "adaptive", "title": "Adaptive Interface", "index": 4},
    {"id": "transitions", "title": "Transitions", "index": 5},
    {"id": "rules", "title": "Global Experience Rules", "index": 6},
    {"id": "cognitive", "title": "Cognitive Load Control", "index": 7},
    {"id": "workspaces", "title": "Multi-Workspace Experience", "index": 8},
    {"id": "accessibility", "title": "Accessibility", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

EXPERIENCE_COMPONENTS = (
    "Experience Engine",
    "Experience Registry",
    "Experience Controller",
    "Experience API",
)

UNIFIED_SUBSYSTEMS = (
    "Visual Director Engine",
    "Visual Story Engine",
    "Visual Simulation Engine",
    "Visual Intelligence Engine",
    "Visual Theme Engine",
    "Visual Asset Registry",
    "Visual Rendering Engine",
)

USER_CONTEXTS = (
    "Executive Context",
    "Manager Context",
    "Operator Context",
    "Developer Context",
    "Administrator Context",
    "Guest Context",
)

ADAPTIVE_DIMENSIONS = (
    "Screen Density",
    "Information Density",
    "Animation Level",
    "Interaction Complexity",
    "Workspace Layout",
    "Notification Density",
)

TRANSITION_TYPES = (
    "Workspace Transition",
    "Module Transition",
    "Organization Transition",
    "Dashboard Transition",
    "AI Team Transition",
    "Story Transition",
)

GLOBAL_RULES = (
    "Visual Consistency",
    "Interaction Consistency",
    "Animation Consistency",
    "Navigation Consistency",
    "Theme Consistency",
)

COGNITIVE_CONTROLS = (
    "Information Overload",
    "Notification Overload",
    "Animation Overload",
    "Context Switching Fatigue",
    "Visual Noise",
)

WORKSPACE_FEATURES = (
    "Cross Workspace Navigation",
    "Shared Context",
    "Persistent Session",
    "Live Synchronization",
    "Workspace Memory",
)

ACCESSIBILITY_FEATURES = (
    "Reduced Motion",
    "High Contrast",
    "Large Text",
    "Keyboard Navigation",
    "Screen Reader Metadata",
)

UI_SURFACES = (
    "Experience Center",
    "UX Diagnostics",
    "Interaction Monitor",
    "Context Viewer",
    "Adaptive UI Panel",
)

CONTEXT_PROFILES = {
    "Executive Context": {
        "Screen Density": "comfortable",
        "Information Density": "summary",
        "Animation Level": "subtle",
        "Interaction Complexity": "low",
        "Workspace Layout": "executive",
        "Notification Density": "critical_only",
    },
    "Manager Context": {
        "Screen Density": "comfortable",
        "Information Density": "balanced",
        "Animation Level": "moderate",
        "Interaction Complexity": "medium",
        "Workspace Layout": "ops",
        "Notification Density": "important",
    },
    "Operator Context": {
        "Screen Density": "compact",
        "Information Density": "detailed",
        "Animation Level": "moderate",
        "Interaction Complexity": "medium",
        "Workspace Layout": "console",
        "Notification Density": "active",
    },
    "Developer Context": {
        "Screen Density": "compact",
        "Information Density": "detailed",
        "Animation Level": "minimal",
        "Interaction Complexity": "high",
        "Workspace Layout": "tools",
        "Notification Density": "verbose",
    },
    "Administrator Context": {
        "Screen Density": "comfortable",
        "Information Density": "balanced",
        "Animation Level": "subtle",
        "Interaction Complexity": "high",
        "Workspace Layout": "admin",
        "Notification Density": "system",
    },
    "Guest Context": {
        "Screen Density": "comfortable",
        "Information Density": "minimal",
        "Animation Level": "subtle",
        "Interaction Complexity": "low",
        "Workspace Layout": "guided",
        "Notification Density": "none",
    },
}


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "components": list(EXPERIENCE_COMPONENTS),
        "unified_subsystems": list(UNIFIED_SUBSYSTEMS),
        "user_contexts": list(USER_CONTEXTS),
        "adaptive_dimensions": list(ADAPTIVE_DIMENSIONS),
        "transition_types": list(TRANSITION_TYPES),
        "global_rules": list(GLOBAL_RULES),
        "cognitive_controls": list(COGNITIVE_CONTROLS),
        "workspace_features": list(WORKSPACE_FEATURES),
        "accessibility_features": list(ACCESSIBILITY_FEATURES),
        "ui_surfaces": list(UI_SURFACES),
        "executes_business_logic": False,
        "presentation_coordination_only": True,
        "enterprise_design_system": True,
        "dark_mode": True,
        "responsive": True,
        "accessibility_ready": True,
        "high_performance": True,
        "gpu_optimized": True,
    }
