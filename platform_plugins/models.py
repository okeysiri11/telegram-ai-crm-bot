# Plugin domain models.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PluginState(str, Enum):
    DISCOVERED = "discovered"
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    FAILED = "failed"
    UNINSTALLED = "uninstalled"


@dataclass
class DependencySpec:
    plugin_id: str
    version: str = "*"
    optional: bool = False


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str
    author: str
    description: str
    platform_version: str
    dependencies: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)
    configuration: dict[str, Any] = field(default_factory=dict)
    routes: list[dict[str, str]] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    entry_point: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def required_dependencies(self) -> list[DependencySpec]:
        return [
            DependencySpec(d["id"], d.get("version", "*"), optional=False)
            for d in self.dependencies.get("required", [])
            if isinstance(d, dict) and d.get("id")
        ]

    @property
    def optional_dependencies(self) -> list[DependencySpec]:
        return [
            DependencySpec(d["id"], d.get("version", "*"), optional=True)
            for d in self.dependencies.get("optional", [])
            if isinstance(d, dict) and d.get("id")
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "platform_version": self.platform_version,
            "dependencies": self.dependencies,
            "permissions": self.permissions,
            "configuration": self.configuration,
            "routes": self.routes,
            "workflows": self.workflows,
            "entry_point": self.entry_point,
        }


@dataclass
class PluginHealth:
    plugin_id: str
    status: str
    message: str = ""
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "status": self.status,
            "message": self.message,
            "checked_at": self.checked_at,
            "details": self.details,
        }


@dataclass
class PluginRecord:
    manifest: PluginManifest
    path: str
    state: PluginState = PluginState.DISCOVERED
    installed_at: str | None = None
    enabled_at: str | None = None
    disabled_at: str | None = None
    last_error: str | None = None
    health: PluginHealth | None = None
    loaded: bool = False
    logs: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.manifest.id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.manifest.name,
            "version": self.manifest.version,
            "author": self.manifest.author,
            "description": self.manifest.description,
            "state": self.state.value,
            "path": self.path,
            "installed_at": self.installed_at,
            "enabled_at": self.enabled_at,
            "disabled_at": self.disabled_at,
            "last_error": self.last_error,
            "health": self.health.to_dict() if self.health else None,
            "loaded": self.loaded,
            "permissions": self.manifest.permissions,
            "dependencies": self.manifest.dependencies,
            "workflows": self.manifest.workflows,
            "routes": self.manifest.routes,
            "logs": self.logs[-20:],
        }
