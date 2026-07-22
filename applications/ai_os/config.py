# AI Operating System — Sprint 12.4.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AIOSConfig:
    application_name: str = "AI Operating System"
    application: str = "ai_os"
    application_version: str = "3.4.0-alpha"
    release_status: str = "AI OS Alpha"
    platform_dependency: str = "AI Platform Core v3.0"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    api_version: str = "v1"
    api_prefix: str = "/api/ai-os/v1"
    internal_prefix: str = "/internal/ai-os/v1"
    ai_kernel: str = "1.0"
    process_manager: str = "1.0"
    system_bus: str = "1.0"
    memory_management: str = "1.0"
    ai_runtime: str = "1.0"
    ai_communication: str = "1.0"
    enterprise: str = "1.0"
    observability: str = "1.0"
    schedulers: list[str] = field(
        default_factory=lambda: [
            "system",
            "task",
            "resource",
            "agent",
            "memory",
            "workflow",
        ]
    )
    buses: list[str] = field(
        default_factory=lambda: [
            "event",
            "message",
            "knowledge",
            "workflow",
            "memory",
            "plugin",
            "connector",
        ]
    )
    memory_tiers: list[str] = field(
        default_factory=lambda: [
            "global",
            "shared",
            "semantic_cache",
            "long_term",
            "session",
            "vector",
            "knowledge_cache",
        ]
    )


DEFAULT_CONFIG = AIOSConfig()
