# PlatformPlugin — abstract base class for business plugins.

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar

from platform_plugin_sdk.models import PluginHealthResult
from platform_plugin_sdk.plugin_hooks import HookName

if TYPE_CHECKING:
    from platform_plugin_sdk.plugin_context import PluginContext


class PlatformPlugin(ABC):
    """
    Base class for all business plugins.

    Subclass this — never import Platform Core modules directly.
    """

    plugin_id: ClassVar[str] = ""
    name: ClassVar[str] = ""
    version: ClassVar[str] = "1.0.0"

    def __init__(self) -> None:
        self._ctx: PluginContext | None = None
        self._started = False

    @property
    def context(self) -> PluginContext:
        if self._ctx is None:
            from platform_plugin_sdk.exceptions import PluginLifecycleError

            raise PluginLifecycleError("Plugin not initialized — call initialize() first")
        return self._ctx

    def configure(self, ctx: PluginContext) -> None:
        """Wire context and register hooks."""
        self._ctx = ctx
        for hook in HookName:
            method = getattr(self, hook.value)
            ctx.hooks.register(hook, method)

    # ---- Lifecycle ----

    async def initialize(self) -> None:
        """Called once when plugin entry is loaded."""
        self.context.logger.info("initialize")

    async def start(self) -> None:
        """Called when plugin is enabled."""
        self._started = True
        self.context.hooks.wire_platform_events(self.context)
        await self.on_enable(self.context)
        self.context.logger.info("start")

    async def stop(self) -> None:
        """Called when plugin is disabled."""
        await self.on_disable(self.context)
        self.context.hooks.unwire_platform_events()
        self._started = False
        self.context.logger.info("stop")

    async def reload(self) -> None:
        """Called on hot reload."""
        await self.on_reload(self.context)
        self.context.logger.info("reload")

    async def health(self) -> PluginHealthResult:
        return PluginHealthResult(status="healthy", message=f"{self.plugin_id or self.context.plugin_id} operational")

    async def shutdown(self) -> None:
        """Called on uninstall."""
        await self.on_disable(self.context)
        self.context.logger.info("shutdown")

    # ---- Hooks (override in subclass) ----

    async def on_install(self, ctx: PluginContext) -> None:
        pass

    async def on_enable(self, ctx: PluginContext) -> None:
        pass

    async def on_disable(self, ctx: PluginContext) -> None:
        pass

    async def on_reload(self, ctx: PluginContext) -> None:
        pass

    async def on_request_created(self, ctx: PluginContext, *, event: Any = None) -> None:
        pass

    async def on_request_completed(self, ctx: PluginContext, *, event: Any = None) -> None:
        pass

    async def on_workflow_started(self, ctx: PluginContext, *, event: Any = None) -> None:
        pass

    async def on_workflow_completed(self, ctx: PluginContext, *, event: Any = None) -> None:
        pass

    async def on_configuration_changed(self, ctx: PluginContext, *, event: Any = None) -> None:
        pass

    async def on_job_completed(self, ctx: PluginContext, *, event: Any = None) -> None:
        pass

    async def on_event(self, ctx: PluginContext, *, event: Any = None) -> None:
        pass
