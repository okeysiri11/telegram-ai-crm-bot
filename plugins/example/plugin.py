"""Example plugin — built entirely with the Plugin SDK."""

from __future__ import annotations

from platform_plugin_sdk import PlatformPlugin, PluginContext
from platform_plugin_sdk.models import PluginHealthResult


class ExamplePlugin(PlatformPlugin):
    plugin_id = "example"
    name = "Example Domain"
    version = "1.0.0"

    async def initialize(self) -> None:
        await super().initialize()
        self.context.storage.set("initialized", True)
        self.context.metrics.increment("initialized")

    async def on_enable(self, ctx: PluginContext) -> None:
        ctx.logger.info("Example plugin enabled")
        await ctx.realtime.publish_plugin_status("enabled", {"example": True})

    async def on_request_created(self, ctx: PluginContext, *, event=None) -> None:
        ctx.logger.info("request created", event_type=getattr(event, "event_type", None))
        ctx.metrics.increment("requests.created")

    async def health(self) -> PluginHealthResult:
        initialized = self.context.storage.get("initialized", False)
        return PluginHealthResult(
            status="healthy" if initialized else "degraded",
            message="Example plugin operational",
            details={"initialized": initialized},
        )


def create_plugin() -> PlatformPlugin:
    return ExamplePlugin()
