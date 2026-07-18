# Plugin system exceptions.

from __future__ import annotations


class PluginError(Exception):
    """Base plugin error."""


class PluginNotFoundError(PluginError):
    def __init__(self, plugin_id: str) -> None:
        super().__init__(f"Plugin not found: {plugin_id}")
        self.plugin_id = plugin_id


class PluginValidationError(PluginError):
    pass


class PluginDependencyError(PluginError):
    pass


class PluginCycleError(PluginDependencyError):
    pass


class PluginLifecycleError(PluginError):
    pass


class PluginLoadError(PluginError):
    pass
