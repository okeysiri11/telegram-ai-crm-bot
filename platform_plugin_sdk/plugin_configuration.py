# Plugin-specific configuration — validation, defaults, versioning.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platform_plugin_sdk.exceptions import PluginConfigurationError
from platform_plugin_sdk.models import PluginConfigSchema


class PluginConfiguration:
    """Manages plugin-private configuration separate from platform config."""

    def __init__(
        self,
        plugin_id: str,
        schema: PluginConfigSchema | None = None,
        config_dir: Path | None = None,
    ) -> None:
        self.plugin_id = plugin_id
        self.schema = schema or PluginConfigSchema()
        self.config_dir = config_dir or Path("plugins") / plugin_id / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._path = self.config_dir / "settings.json"
        self._cache: dict[str, Any] | None = None

    def load(self) -> dict[str, Any]:
        raw: dict[str, Any] = {}
        if self._path.is_file():
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        merged = self.schema.validate({**self.schema.defaults, **raw})
        self._cache = merged
        return merged

    def save(self, config: dict[str, Any]) -> dict[str, Any]:
        validated = self.schema.validate(config)
        self._path.write_text(json.dumps(validated, indent=2), encoding="utf-8")
        self._cache = validated
        return validated

    def get(self, key: str, default: Any = None) -> Any:
        if self._cache is None:
            self.load()
        assert self._cache is not None
        return self._cache.get(key, default)

    def set(self, key: str, value: Any) -> None:
        current = self.load()
        current[key] = value
        self.save(current)

    def upgrade_schema(self, new_schema: PluginConfigSchema) -> dict[str, Any]:
        current = self.load()
        if new_schema.version < self.schema.version:
            raise PluginConfigurationError("Cannot downgrade configuration schema version")
        self.schema = new_schema
        return self.save(current)
