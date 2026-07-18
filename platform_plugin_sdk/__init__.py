# Platform Plugin SDK — official extension API for business plugins.

from platform_plugin_sdk.plugin import PlatformPlugin
from platform_plugin_sdk.plugin_builder import PluginBuilder, build_plugin_context
from platform_plugin_sdk.plugin_context import PluginContext
from platform_plugin_sdk.models import (
    PluginConfigSchema,
    PluginHealthResult,
    PluginMetadata,
)
from platform_plugin_sdk.plugin_events import (
    PluginEvent,
    PluginHealth,
    PluginMetric,
    PluginNotification,
)
from platform_plugin_sdk.exceptions import PluginSdkError

__all__ = [
    "PlatformPlugin",
    "PluginBuilder",
    "PluginContext",
    "PluginConfigSchema",
    "PluginHealthResult",
    "PluginMetadata",
    "PluginEvent",
    "PluginHealth",
    "PluginMetric",
    "PluginNotification",
    "PluginSdkError",
    "build_plugin_context",
]

SDK_VERSION = "1.0.0"
