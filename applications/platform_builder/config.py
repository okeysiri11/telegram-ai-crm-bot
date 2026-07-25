"""Platform Builder — Sprint 29.1 AI Operations Center."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PlatformBuilderConfig:
    application_name: str = "Platform Builder"
    application: str = "platform_builder"
    application_version: str = "1.8.0"
    sprint: str = "29.1"
    release_status: str = "AI Operations Center"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v8.7.0"
    api_version: str = "v1"
    api_prefix: str = "/api/platform-builder/v1"
    internal_prefix: str = "/internal/platform-builder/v1"
    builder_engine: str = "1.0"
    builder_academy: str = "2.0"
    god_mode: str = "2.0"
    help_system: str = "1.0"
    ai_builder: str = "1.0"
    concierge_builder: str = "1.0"
    ai_team_center: str = "1.0"
    vertical_builder: str = "1.0"
    universal_builder_framework: str = "1.0"
    builder_sdk: str = "0.1"
    ai_guide: str = "1.0"
    platform_control_center: str = "1.0"
    collaborative_ai: str = "1.0"
    collective_intelligence: str = "1.0"
    operations_center: str = "1.0"
    visual_layer: str = "1.0"
    live_status_engine: str = "1.0"
    platform_owner_role: str = "platform_owner"
    academy_modes: list[str] = field(
        default_factory=lambda: ["quick_start", "guided_learning", "expert"]
    )
    experience_levels: list[str] = field(
        default_factory=lambda: ["beginner", "intermediate", "advanced", "expert"]
    )
    framework_phases: list[str] = field(
        default_factory=lambda: [
            "step",
            "explanation",
            "information",
            "example",
            "preview",
            "create",
        ]
    )
    universal_lifecycle: list[str] = field(
        default_factory=lambda: [
            "initialize",
            "configure",
            "validate",
            "preview",
            "summary",
            "create",
            "register",
            "finish",
        ]
    )


DEFAULT_CONFIG = PlatformBuilderConfig()
