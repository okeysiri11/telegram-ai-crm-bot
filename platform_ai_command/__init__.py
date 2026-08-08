"""Epic 44.0 — AI Command Center (Universal AI Operating System).

All execution MUST go through Hercules Runtime. Never call providers directly.
"""

from __future__ import annotations

VERSION = "44.0.0"
EPIC = "AI_COMMAND_CENTER_44.0"


def __getattr__(name: str):
    if name in ("AiCommandCenter", "ai_command_center"):
        from platform_ai_command.core.command_center import AiCommandCenter, ai_command_center

        return AiCommandCenter if name == "AiCommandCenter" else ai_command_center
    raise AttributeError(name)


__all__ = ["AiCommandCenter", "ai_command_center", "VERSION", "EPIC"]
