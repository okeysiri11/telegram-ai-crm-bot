# Configuration & Deployment Layer — platform events.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class ConfigurationLoadedEvent(BaseEvent):
    environment: str = ""
    key_count: int = 0
    duration_ms: float = 0.0


@dataclass(kw_only=True)
class DeploymentCompletedEvent(BaseEvent):
    deployment_id: str = ""
    target: str = ""
    status: str = ""
    duration_ms: float = 0.0


@dataclass(kw_only=True)
class MigrationAppliedEvent(BaseEvent):
    migration_id: str = ""
    direction: str = ""
    version_to: str = ""


@dataclass(kw_only=True)
class FeatureFlagChangedEvent(BaseEvent):
    flag_key: str = ""
    enabled: bool = False
    metadata: dict[str, Any] | None = None


@dataclass(kw_only=True)
class EnvironmentActivatedEvent(BaseEvent):
    environment: str = ""
    isolated: bool = False
