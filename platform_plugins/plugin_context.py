# PluginContext — delegates to Plugin SDK (stable public API).

from __future__ import annotations

from platform_plugin_sdk.plugin_builder import build_plugin_context
from platform_plugin_sdk.plugin_context import PluginContext

PLATFORM_VERSION = "1.0.0"

__all__ = ["PluginContext", "build_plugin_context", "PLATFORM_VERSION"]
