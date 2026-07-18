# In-memory plugin registry.

from __future__ import annotations

from platform_plugins.exceptions import PluginNotFoundError
from platform_plugins.models import PluginRecord, PluginState


class PluginRegistry:
    def __init__(self) -> None:
        self._records: dict[str, PluginRecord] = {}

    def register(self, record: PluginRecord) -> None:
        self._records[record.id] = record

    def get(self, plugin_id: str) -> PluginRecord:
        if plugin_id not in self._records:
            raise PluginNotFoundError(plugin_id)
        return self._records[plugin_id]

    def get_optional(self, plugin_id: str) -> PluginRecord | None:
        return self._records.get(plugin_id)

    def all(self) -> dict[str, PluginRecord]:
        return dict(self._records)

    def list_by_state(self, *states: PluginState) -> list[PluginRecord]:
        return [r for r in self._records.values() if r.state in states]

    def remove(self, plugin_id: str) -> None:
        self._records.pop(plugin_id, None)

    def clear(self) -> None:
        self._records.clear()


plugin_registry = PluginRegistry()
