"""Enterprise Command Center OS catalogs — Sprint 29.13."""

from __future__ import annotations

from typing import Any


WIZARD_STEPS = [
    {"id": "core", "title": "Command Center Core", "index": 1},
    {"id": "palette", "title": "Global Command Palette", "index": 2},
    {"id": "execution", "title": "Command Execution", "index": 3},
    {"id": "categories", "title": "Command Categories", "index": 4},
    {"id": "voice", "title": "Voice Foundation", "index": 5},
    {"id": "hotkeys", "title": "Hotkey Engine", "index": 6},
    {"id": "history", "title": "Command History", "index": 7},
    {"id": "assistant", "title": "AI Command Assistant", "index": 8},
    {"id": "performance", "title": "Performance", "index": 9},
    {"id": "create", "title": "Create", "index": 10},
]

COMMAND_CENTER_COMPONENTS = (
    "Command Center",
    "Command Registry",
    "Command Dispatcher",
    "Command API",
    "Command History",
)

PALETTE_FEATURES = (
    "Universal Search",
    "Open Module",
    "Open Workspace",
    "Open AI",
    "Open Organization",
    "Recent Commands",
    "Favorite Commands",
)

EXECUTION_TYPES = (
    "Workspace Commands",
    "AI Commands",
    "Document Commands",
    "Workflow Commands",
    "Builder Commands",
    "Organization Commands",
)

COMMAND_CATEGORIES = (
    "Navigation",
    "Administration",
    "Analytics",
    "AI",
    "Knowledge",
    "Projects",
    "Marketplace",
    "Development",
    "Security",
)

VOICE_APIS = (
    "Voice Commands",
    "Speech Recognition Interface",
    "Speech Feedback",
    "Future Voice Assistant",
)

HOTKEY_FEATURES = (
    "Global Shortcuts",
    "Workspace Shortcuts",
    "Module Shortcuts",
    "Custom Shortcuts",
    "Shortcut Profiles",
)

HISTORY_FEATURES = (
    "History",
    "Frequently Used",
    "Pinned Commands",
    "Favorites",
    "Suggestions",
)

ASSISTANT_FEATURES = (
    "Natural Language Commands",
    "Command Suggestions",
    "Auto Complete",
    "Context Aware Commands",
    "Smart Recommendations",
)

PERFORMANCE_FEATURES = (
    "Command Cache",
    "Fast Search",
    "Lazy Loading",
    "Index Optimization",
    "Realtime Suggestions",
)

UI_SURFACES = (
    "Command Palette",
    "Quick Launcher",
    "Command History",
    "Shortcut Manager",
    "Voice Console",
    "AI Suggestions",
)

DEFAULT_COMMANDS = (
    {
        "id": "cmd_open_ops",
        "title": "Open AI Operations Center",
        "category": "AI",
        "execution_type": "AI Commands",
        "keywords": ("ops", "operations", "ai"),
    },
    {
        "id": "cmd_open_workspace",
        "title": "Open Workspace OS",
        "category": "Navigation",
        "execution_type": "Workspace Commands",
        "keywords": ("workspace", "os"),
    },
    {
        "id": "cmd_open_builder",
        "title": "Open Builder Studio",
        "category": "Development",
        "execution_type": "Builder Commands",
        "keywords": ("builder", "studio"),
    },
    {
        "id": "cmd_open_org",
        "title": "Open Organization Map",
        "category": "Administration",
        "execution_type": "Organization Commands",
        "keywords": ("organization", "map"),
    },
    {
        "id": "cmd_search_knowledge",
        "title": "Search Knowledge Center",
        "category": "Knowledge",
        "execution_type": "Document Commands",
        "keywords": ("knowledge", "docs"),
    },
    {
        "id": "cmd_run_analytics",
        "title": "Open Analytics Center",
        "category": "Analytics",
        "execution_type": "Workflow Commands",
        "keywords": ("analytics", "insights"),
    },
    {
        "id": "cmd_marketplace",
        "title": "Open Marketplace",
        "category": "Marketplace",
        "execution_type": "Organization Commands",
        "keywords": ("marketplace", "store"),
    },
    {
        "id": "cmd_security",
        "title": "Open Security Console",
        "category": "Security",
        "execution_type": "Organization Commands",
        "keywords": ("security", "access"),
    },
)

DEFAULT_SHORTCUTS = {
    "Global Shortcuts": {"command_palette": "Cmd+K", "quick_launcher": "Cmd+Shift+P"},
    "Workspace Shortcuts": {"switch_workspace": "Cmd+1", "new_workspace": "Cmd+Shift+N"},
    "Module Shortcuts": {"ops": "Cmd+O", "team_map": "Cmd+T"},
}


def full_catalog() -> dict[str, Any]:
    return {
        "steps": WIZARD_STEPS,
        "components": list(COMMAND_CENTER_COMPONENTS),
        "palette_features": list(PALETTE_FEATURES),
        "execution_types": list(EXECUTION_TYPES),
        "categories": list(COMMAND_CATEGORIES),
        "voice_apis": list(VOICE_APIS),
        "hotkey_features": list(HOTKEY_FEATURES),
        "history_features": list(HISTORY_FEATURES),
        "assistant_features": list(ASSISTANT_FEATURES),
        "performance_features": list(PERFORMANCE_FEATURES),
        "ui_surfaces": list(UI_SURFACES),
        "default_commands": [dict(c) for c in DEFAULT_COMMANDS],
        "default_shortcuts": {k: dict(v) for k, v in DEFAULT_SHORTCUTS.items()},
        "enterprise_design_system": True,
        "dark_mode": True,
        "responsive": True,
        "keyboard_first": True,
        "voice_ready": True,
        "ai_native": True,
        "executes_business_logic": False,
        "orchestrates_user_interaction_only": True,
    }
