# Configuration & Deployment Layer — core models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class EnvironmentProfile(str, enum.Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    CUSTOM = "custom"


class DeploymentTarget(str, enum.Enum):
    LOCAL = "local"
    DOCKER = "docker"


class DeploymentStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    VERIFIED = "verified"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class MigrationDirection(str, enum.Enum):
    UP = "up"
    DOWN = "down"


@dataclass
class ConfigurationSnapshot:
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    environment: str = "development"
    values: dict[str, Any] = field(default_factory=dict)
    encrypted_keys: set[str] = field(default_factory=set)
    schema_version: str = "1.0"
    created_at: float = field(default_factory=time.time)
    source_layers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "environment": self.environment,
            "values": dict(self.values),
            "encrypted_keys": sorted(self.encrypted_keys),
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "source_layers": list(self.source_layers),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfigurationSnapshot:
        return cls(
            snapshot_id=data.get("snapshot_id", str(uuid.uuid4())),
            environment=data.get("environment", "development"),
            values=dict(data.get("values", {})),
            encrypted_keys=set(data.get("encrypted_keys", [])),
            schema_version=data.get("schema_version", "1.0"),
            created_at=float(data.get("created_at", time.time())),
            source_layers=list(data.get("source_layers", [])),
        )


@dataclass
class FeatureFlag:
    key: str
    enabled: bool = False
    rollout_percent: float = 100.0
    experimental: bool = False
    agent_ids: set[str] = field(default_factory=set)
    workflow_ids: set[str] = field(default_factory=set)
    user_ids: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "enabled": self.enabled,
            "rollout_percent": self.rollout_percent,
            "experimental": self.experimental,
            "agent_ids": sorted(self.agent_ids),
            "workflow_ids": sorted(self.workflow_ids),
            "user_ids": sorted(self.user_ids),
            "metadata": dict(self.metadata),
        }


@dataclass
class DeploymentRecord:
    deployment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target: DeploymentTarget = DeploymentTarget.LOCAL
    environment: str = "development"
    status: DeploymentStatus = DeploymentStatus.PENDING
    version: str = ""
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    duration_ms: float = 0.0
    verification: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "deployment_id": self.deployment_id,
            "target": self.target.value,
            "environment": self.environment,
            "status": self.status.value,
            "version": self.version,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "verification": dict(self.verification),
            "metadata": dict(self.metadata),
        }


@dataclass
class MigrationRecord:
    migration_id: str
    version_from: str
    version_to: str
    direction: MigrationDirection
    applied_at: float = field(default_factory=time.time)
    success: bool = True
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "migration_id": self.migration_id,
            "version_from": self.version_from,
            "version_to": self.version_to,
            "direction": self.direction.value,
            "applied_at": self.applied_at,
            "success": self.success,
            "message": self.message,
        }


@dataclass
class VersionInfo:
    platform_version: str = "2.8.0-alpha"
    configuration_layer: str = "1.0"
    deployment_framework: str = "1.0"
    feature_flags: str = "1.0"
    components: dict[str, str] = field(default_factory=dict)
    schema_version: str = "1.0"
    compatible: bool = True
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform_version": self.platform_version,
            "configuration_layer": self.configuration_layer,
            "deployment_framework": self.deployment_framework,
            "feature_flags": self.feature_flags,
            "components": dict(self.components),
            "schema_version": self.schema_version,
            "compatible": self.compatible,
            "issues": list(self.issues),
        }
