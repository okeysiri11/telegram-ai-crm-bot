"""Platform Builder — Sprint 28.3 Enterprise AI Concierge."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PlatformBuilderConfig:
    application_name: str = "Platform Builder"
    application: str = "platform_builder"
    application_version: str = "1.2.0"
    sprint: str = "28.3"
    release_status: str = "Enterprise AI Concierge"
    platform_dependency: str = "AI Platform Core v3"
    enterprise_foundation: str = "Enterprise Platform v8.7.0"
    api_version: str = "v1"
    api_prefix: str = "/api/platform-builder/v1"
    internal_prefix: str = "/internal/platform-builder/v1"
    builder_engine: str = "1.0"
    builder_academy: str = "1.0"
    god_mode: str = "1.0"
    help_system: str = "1.0"
    ai_builder: str = "1.0"
    concierge_builder: str = "1.0"
    platform_owner_role: str = "platform_owner"
    academy_modes: list[str] = field(
        default_factory=lambda: ["quick_start", "guided_learning", "expert"]
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


DEFAULT_CONFIG = PlatformBuilderConfig()
