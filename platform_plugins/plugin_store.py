# Plugin state persistence (file-backed).

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from platform_plugins.models import PluginRecord, PluginState

logger = logging.getLogger(__name__)


class PluginStore:
    """Persists installed/enabled state across restarts."""

    def __init__(self, store_path: Path | None = None) -> None:
        self._path = store_path or Path("plugins/.plugin_store.json")
        self._data: dict[str, Any] = {"installed": {}, "enabled": []}

    def load(self) -> None:
        if not self._path.is_file():
            return
        try:
            self._data = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("plugin_store_load_failed error=%s", exc)

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def mark_installed(self, record: PluginRecord) -> None:
        self._data.setdefault("installed", {})[record.id] = {
            "version": record.manifest.version,
            "installed_at": record.installed_at,
            "path": record.path,
        }
        self.save()

    def mark_uninstalled(self, plugin_id: str) -> None:
        self._data.get("installed", {}).pop(plugin_id, None)
        enabled = self._data.get("enabled", [])
        if plugin_id in enabled:
            enabled.remove(plugin_id)
        self.save()

    def mark_enabled(self, plugin_id: str) -> None:
        enabled: list[str] = self._data.setdefault("enabled", [])
        if plugin_id not in enabled:
            enabled.append(plugin_id)
        self.save()

    def mark_disabled(self, plugin_id: str) -> None:
        enabled: list[str] = self._data.setdefault("enabled", [])
        if plugin_id in enabled:
            enabled.remove(plugin_id)
        self.save()

    def installed_ids(self) -> set[str]:
        return set(self._data.get("installed", {}).keys())

    def enabled_ids(self) -> set[str]:
        return set(self._data.get("enabled", []))

    def apply_persisted_state(self, records: dict[str, PluginRecord]) -> None:
        for plugin_id in self.installed_ids():
            record = records.get(plugin_id)
            if record:
                record.state = PluginState.INSTALLED
                info = self._data["installed"].get(plugin_id, {})
                record.installed_at = info.get("installed_at")
        for plugin_id in self.enabled_ids():
            record = records.get(plugin_id)
            if record and record.state == PluginState.INSTALLED:
                record.state = PluginState.ENABLED


plugin_store = PluginStore()
