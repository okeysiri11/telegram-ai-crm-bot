# Platform Plugin System — installable business domain modules.

from platform_plugins.plugin_manager import plugin_manager
from platform_plugins.models import PluginRecord, PluginState

__all__ = ["plugin_manager", "PluginRecord", "PluginState"]
