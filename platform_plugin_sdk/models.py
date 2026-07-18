# Public SDK models — stable dataclasses for plugin developers.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PluginMetadata:
    plugin_id: str
    name: str
    version: str
    author: str = ""
    description: str = ""
    permissions: list[str] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)


@dataclass
class PluginHealthResult:
    status: str = "healthy"
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "message": self.message, "details": self.details}


@dataclass
class PluginConfigSchema:
    """Declarative plugin configuration with defaults and validation."""

    version: int = 1
    defaults: dict[str, Any] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)
    properties: dict[str, dict[str, Any]] = field(default_factory=dict)

    def validate(self, config: dict[str, Any]) -> dict[str, Any]:
        merged = {**self.defaults, **config}
        missing = [k for k in self.required if k not in merged]
        if missing:
            from platform_plugin_sdk.exceptions import PluginConfigurationError

            raise PluginConfigurationError(f"Missing required config keys: {', '.join(missing)}")
        for key, spec in self.properties.items():
            if key not in merged:
                continue
            expected = spec.get("type")
            value = merged[key]
            if expected == "string" and not isinstance(value, str):
                raise PluginConfigurationError(f"{key} must be a string")
            if expected == "integer" and not isinstance(value, int):
                raise PluginConfigurationError(f"{key} must be an integer")
            if expected == "boolean" and not isinstance(value, bool):
                raise PluginConfigurationError(f"{key} must be a boolean")
        return merged
