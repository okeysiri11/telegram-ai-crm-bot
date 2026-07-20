# Configuration & Deployment Layer — default settings.

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConfigurationLayerConfig:
    schema_version: str = "1.0"
    default_environment: str = "development"
    enable_encryption: bool = True
    enable_runtime_updates: bool = True
    deployment_verify_timeout_sec: float = 30.0
    docker_image: str = "platform:latest"
    migration_auto_apply: bool = False


DEFAULT_LAYER_CONFIG = ConfigurationLayerConfig()
