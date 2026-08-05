"""Enterprise Service Builder domain models — Sprint 36.0."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ServiceState(str, Enum):
    DRAFT = "draft"
    INSTALLED = "installed"
    LOADED = "loaded"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    DISABLED = "disabled"
    UPDATING = "updating"
    REMOVING = "removing"


class ServiceCategory(str, Enum):
    RUNTIME = "runtime"
    INFRASTRUCTURE = "infrastructure"
    AI = "ai"
    WORKFLOW = "workflow"
    EVENT = "event"
    INTEGRATION = "integration"
    SECURITY = "security"
    BUSINESS = "business"
    CREATIVE = "creative"
    CITY = "city"
    OTHER = "other"


VALID_TRANSITIONS: dict[ServiceState, set[ServiceState]] = {
    ServiceState.DRAFT: {ServiceState.INSTALLED, ServiceState.REMOVING},
    ServiceState.INSTALLED: {
        ServiceState.LOADED,
        ServiceState.DISABLED,
        ServiceState.UPDATING,
        ServiceState.REMOVING,
    },
    ServiceState.LOADED: {
        ServiceState.RUNNING,
        ServiceState.DISABLED,
        ServiceState.FAILED,
        ServiceState.UPDATING,
        ServiceState.REMOVING,
    },
    ServiceState.RUNNING: {
        ServiceState.PAUSED,
        ServiceState.LOADED,
        ServiceState.FAILED,
        ServiceState.DISABLED,
        ServiceState.UPDATING,
        ServiceState.REMOVING,
    },
    ServiceState.PAUSED: {
        ServiceState.RUNNING,
        ServiceState.LOADED,
        ServiceState.DISABLED,
        ServiceState.FAILED,
        ServiceState.REMOVING,
    },
    ServiceState.FAILED: {
        ServiceState.LOADED,
        ServiceState.RUNNING,
        ServiceState.DISABLED,
        ServiceState.REMOVING,
        ServiceState.INSTALLED,
    },
    ServiceState.DISABLED: {
        ServiceState.INSTALLED,
        ServiceState.LOADED,
        ServiceState.REMOVING,
    },
    ServiceState.UPDATING: {
        ServiceState.INSTALLED,
        ServiceState.LOADED,
        ServiceState.RUNNING,
        ServiceState.FAILED,
    },
    ServiceState.REMOVING: {ServiceState.DRAFT},
}


@dataclass
class ServicePermissions:
    allowed_apis: list[str] = field(default_factory=list)
    allowed_events: list[str] = field(default_factory=list)
    allowed_storage: list[str] = field(default_factory=list)
    allowed_ai_tools: list[str] = field(default_factory=list)
    allowed_integrations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ServicePermissions:
        data = data or {}
        return cls(
            allowed_apis=list(data.get("allowed_apis") or data.get("apis") or []),
            allowed_events=list(data.get("allowed_events") or data.get("events") or []),
            allowed_storage=list(data.get("allowed_storage") or data.get("storage") or []),
            allowed_ai_tools=list(data.get("allowed_ai_tools") or data.get("ai_tools") or []),
            allowed_integrations=list(
                data.get("allowed_integrations") or data.get("integrations") or []
            ),
        )


@dataclass
class ServiceHealthcheck:
    path: str = "/health"
    interval_sec: int = 30
    timeout_sec: int = 5
    failure_threshold: int = 3

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ServiceHealthcheck:
        data = data or {}
        return cls(
            path=str(data.get("path") or "/health"),
            interval_sec=int(data.get("interval_sec") or 30),
            timeout_sec=int(data.get("timeout_sec") or 5),
            failure_threshold=int(data.get("failure_threshold") or 3),
        )


@dataclass
class ServiceConfiguration:
    settings: dict[str, Any] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)
    feature_flags: dict[str, bool] = field(default_factory=dict)
    resources: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ServiceConfiguration:
        data = data or {}
        return cls(
            settings=dict(data.get("settings") or {}),
            env={str(k): str(v) for k, v in dict(data.get("env") or {}).items()},
            feature_flags={str(k): bool(v) for k, v in dict(data.get("feature_flags") or {}).items()},
            resources=dict(data.get("resources") or {}),
        )


@dataclass
class ServiceManifest:
    """Canonical service package manifest."""

    id: str
    name: str
    display_name: str
    version: str
    description: str = ""
    owner: str = "platform"
    category: str = ServiceCategory.OTHER.value
    permissions: ServicePermissions = field(default_factory=ServicePermissions)
    dependencies: list[str] = field(default_factory=list)
    api: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)
    healthcheck: ServiceHealthcheck = field(default_factory=ServiceHealthcheck)
    icon: str = "box"
    status: str = ServiceState.DRAFT.value
    entrypoint: str | None = None
    module_path: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "version": self.version,
            "description": self.description,
            "owner": self.owner,
            "category": self.category,
            "permissions": self.permissions.to_dict(),
            "dependencies": list(self.dependencies),
            "api": list(self.api),
            "events": list(self.events),
            "settings": dict(self.settings),
            "healthcheck": self.healthcheck.to_dict(),
            "icon": self.icon,
            "status": self.status,
            "entrypoint": self.entrypoint,
            "module_path": self.module_path,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServiceManifest:
        sid = str(data.get("id") or data.get("service_id") or f"svc_{uuid.uuid4().hex[:12]}")
        name = str(data.get("name") or sid)
        return cls(
            id=sid,
            name=name,
            display_name=str(data.get("display_name") or name),
            version=str(data.get("version") or "0.1.0"),
            description=str(data.get("description") or ""),
            owner=str(data.get("owner") or "platform"),
            category=str(data.get("category") or ServiceCategory.OTHER.value),
            permissions=ServicePermissions.from_dict(data.get("permissions")),
            dependencies=list(data.get("dependencies") or []),
            api=list(data.get("api") or []),
            events=list(data.get("events") or []),
            settings=dict(data.get("settings") or {}),
            healthcheck=ServiceHealthcheck.from_dict(data.get("healthcheck")),
            icon=str(data.get("icon") or "box"),
            status=str(data.get("status") or ServiceState.DRAFT.value),
            entrypoint=data.get("entrypoint"),
            module_path=data.get("module_path"),
            tags=list(data.get("tags") or []),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass
class ServiceVersion:
    service_id: str
    version: str
    changelog: str = ""
    created_at: float = field(default_factory=time.time)
    created_by: str = "system"
    manifest_snapshot: dict[str, Any] = field(default_factory=dict)
    is_active: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ServiceDefinition:
    """Registered service record (registry row + runtime fields)."""

    id: str
    manifest: ServiceManifest
    state: ServiceState = ServiceState.DRAFT
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    started_at: float | None = None
    last_heartbeat_at: float | None = None
    restart_count: int = 0
    error_message: str | None = None
    configuration: ServiceConfiguration = field(default_factory=ServiceConfiguration)
    cpu_pct: float = 0.0
    ram_mb: float = 0.0
    response_time_ms: float = 0.0
    availability_pct: float = 100.0
    error_count: int = 0
    loaded_module: str | None = None
    sandbox_id: str | None = None

    @property
    def uptime_sec(self) -> float:
        if self.state != ServiceState.RUNNING or self.started_at is None:
            return 0.0
        return max(0.0, time.time() - self.started_at)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.manifest.name,
            "display_name": self.manifest.display_name,
            "version": self.manifest.version,
            "description": self.manifest.description,
            "owner": self.manifest.owner,
            "category": self.manifest.category,
            "icon": self.manifest.icon,
            "status": self.state.value,
            "state": self.state.value,
            "enabled": self.enabled,
            "dependencies": list(self.manifest.dependencies),
            "api": list(self.manifest.api),
            "events": list(self.manifest.events),
            "permissions": self.manifest.permissions.to_dict(),
            "settings": dict(self.manifest.settings),
            "configuration": self.configuration.to_dict(),
            "healthcheck": self.manifest.healthcheck.to_dict(),
            "cpu": self.cpu_pct,
            "ram": self.ram_mb,
            "uptime": self.uptime_sec,
            "uptime_sec": self.uptime_sec,
            "last_update": self.updated_at,
            "updated_at": self.updated_at,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "last_heartbeat_at": self.last_heartbeat_at,
            "restart_count": self.restart_count,
            "error_message": self.error_message,
            "response_time_ms": self.response_time_ms,
            "availability_pct": self.availability_pct,
            "error_count": self.error_count,
            "loaded_module": self.loaded_module,
            "sandbox_id": self.sandbox_id,
            "tags": list(self.manifest.tags),
            "metadata": dict(self.manifest.metadata),
            "manifest": self.manifest.to_dict(),
        }


@dataclass
class ServiceLogEntry:
    service_id: str
    level: str
    message: str
    actor: str = "system"
    operation: str | None = None
    old_state: str | None = None
    new_state: str | None = None
    duration_ms: float | None = None
    result: str = "ok"
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    log_id: str = field(default_factory=lambda: f"log_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ServiceHealthSnapshot:
    service_id: str
    healthy: bool
    heartbeat_at: float | None
    response_time_ms: float
    memory_mb: float
    cpu_pct: float
    errors: int
    restart_count: int
    availability_pct: float
    status: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DependencyNode:
    service_id: str
    status: str  # healthy | missing | cyclic | disabled
    state: str | None = None
    children: list[DependencyNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_id": self.service_id,
            "status": self.status,
            "state": self.state,
            "children": [c.to_dict() for c in self.children],
        }


def parse_semver(version: str) -> tuple[int, int, int]:
    raw = (version or "0.0.0").strip().lstrip("v")
    parts = raw.split("+")[0].split("-")[0].split(".")
    nums = []
    for i in range(3):
        try:
            nums.append(int(parts[i]) if i < len(parts) else 0)
        except ValueError:
            nums.append(0)
    return nums[0], nums[1], nums[2]


def compare_semver(a: str, b: str) -> int:
    ta, tb = parse_semver(a), parse_semver(b)
    return (ta > tb) - (ta < tb)
