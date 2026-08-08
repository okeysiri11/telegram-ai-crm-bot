"""Sprint 43.4 — Vertical AI Framework.

Config-driven industry AI assistants over UnifiedAiPipeline.
Beauty AI is the first complete reference vertical.
"""

from platform_vertical_ai.framework import VerticalAiFramework, vertical_ai_framework
from platform_vertical_ai.models import VerticalConfig
from platform_vertical_ai.registry import VerticalRegistry, vertical_registry

__all__ = [
    "VerticalAiFramework",
    "vertical_ai_framework",
    "VerticalConfig",
    "VerticalRegistry",
    "vertical_registry",
]
