# Ecosystem configuration — Sprint 7.1.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EcosystemConfig:
    ecosystem_version: str = "1.0.0-alpha"
    platform_dependency: str = "AI Platform Core v3.0"
    api_version: str = "v1"
    api_prefix: str = "/api/ecosystem/v1"
    session_ttl_seconds: int = 86400
    registered_applications: list[str] = field(
        default_factory=lambda: ["auto_marketplace"]
    )


DEFAULT_CONFIG = EcosystemConfig()
