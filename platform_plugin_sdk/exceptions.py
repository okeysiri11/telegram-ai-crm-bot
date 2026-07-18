# Plugin SDK exceptions — public error types.

from __future__ import annotations


class PluginSdkError(Exception):
    """Base SDK error visible to plugin developers."""


class PluginConfigurationError(PluginSdkError):
    pass


class PluginStorageError(PluginSdkError):
    pass


class PluginHookError(PluginSdkError):
    pass


class PluginLifecycleError(PluginSdkError):
    pass


class PluginPermissionError(PluginSdkError):
    pass
