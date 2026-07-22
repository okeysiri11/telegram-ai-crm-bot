# Drone Platform configuration — Sprint 11.1 Foundation.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DronePlatformConfig:
    application_name: str = "Drone Platform"
    application: str = "drone_platform"
    application_version: str = "1.0.0-alpha"
    release_status: str = "Foundation Alpha"
    api_version: str = "v1"
    api_prefix: str = "/api/drone/v1"
    internal_prefix: str = "/internal/drone/v1"
    platform_dependency: str = "AI Platform Core v3"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    registry_engine: str = "1.0"
    engineering_engine: str = "1.0"
    firmware_engine: str = "1.0"
    mission_engine: str = "1.0"
    inventory_engine: str = "1.0"
    ai_engine: str = "1.0"


DEFAULT_CONFIG = DronePlatformConfig()
