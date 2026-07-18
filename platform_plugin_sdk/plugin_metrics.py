# Plugin metrics facade.

from __future__ import annotations

from platform_plugin_sdk.plugin_api import ObservabilityApi
from platform_plugin_sdk.plugin_events import PluginMetric


class PluginMetrics:
    """Emit metrics tagged with plugin_id."""

    def __init__(self, plugin_id: str, observability: ObservabilityApi) -> None:
        self.plugin_id = plugin_id
        self._obs = observability

    def _tags(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        tags = {"plugin_id": self.plugin_id}
        if extra:
            tags.update(extra)
        return tags

    def increment(self, name: str, value: float = 1.0, **tags: str) -> PluginMetric:
        full_name = f"plugin.{self.plugin_id}.{name}"
        self._obs.increment(full_name, value, **self._tags(tags))
        return PluginMetric(plugin_id=self.plugin_id, name=full_name, value=value, tags=self._tags(tags))

    def gauge(self, name: str, value: float, **tags: str) -> PluginMetric:
        full_name = f"plugin.{self.plugin_id}.{name}"
        self._obs.gauge(full_name, value, **self._tags(tags))
        return PluginMetric(plugin_id=self.plugin_id, name=full_name, value=value, tags=self._tags(tags))
