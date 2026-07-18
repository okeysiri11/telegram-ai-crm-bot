# Namespaced plugin storage with migrations and isolation.

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable

from platform_plugin_sdk.exceptions import PluginStorageError

logger = logging.getLogger(__name__)

MigrationFn = Callable[[dict[str, Any]], dict[str, Any]]

DEFAULT_ROOT = Path("plugins/.storage")


class PluginStorage:
    """Isolated key-value storage per plugin — never shared between plugins."""

    def __init__(self, plugin_id: str, root: Path | None = None) -> None:
        self.plugin_id = plugin_id
        self.root = (root or DEFAULT_ROOT) / plugin_id
        self.root.mkdir(parents=True, exist_ok=True)
        self._meta_path = self.root / "_meta.json"
        self._data_path = self.root / "data.json"
        self._migrations: dict[int, MigrationFn] = {}

    def register_migration(self, version: int, fn: MigrationFn) -> None:
        self._migrations[version] = fn

    def _load_meta(self) -> dict[str, Any]:
        if not self._meta_path.is_file():
            return {"version": 0}
        return json.loads(self._meta_path.read_text(encoding="utf-8"))

    def _save_meta(self, meta: dict[str, Any]) -> None:
        self._meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    def _load_data(self) -> dict[str, Any]:
        if not self._data_path.is_file():
            return {}
        return json.loads(self._data_path.read_text(encoding="utf-8"))

    def _save_data(self, data: dict[str, Any]) -> None:
        self._data_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def migrate(self, target_version: int) -> int:
        meta = self._load_meta()
        current = int(meta.get("version", 0))
        data = self._load_data()

        while current < target_version:
            next_version = current + 1
            fn = self._migrations.get(next_version)
            if fn:
                data = fn(data)
            current = next_version

        meta["version"] = current
        self._save_meta(meta)
        self._save_data(data)
        logger.info("plugin_storage_migrated plugin=%s version=%s", self.plugin_id, current)
        return current

    def get(self, key: str, default: Any = None) -> Any:
        return self._load_data().get(key, default)

    def set(self, key: str, value: Any) -> None:
        data = self._load_data()
        data[key] = value
        self._save_data(data)

    def delete(self, key: str) -> None:
        data = self._load_data()
        data.pop(key, None)
        self._save_data(data)

    def all(self) -> dict[str, Any]:
        return dict(self._load_data())

    def clear(self) -> None:
        if self._data_path.is_file():
            self._data_path.unlink()
        if self._meta_path.is_file():
            self._meta_path.unlink()

    @property
    def version(self) -> int:
        return int(self._load_meta().get("version", 0))
