# PluginBuilder — constructs PluginContext and PlatformPlugin instances.

from __future__ import annotations

from pathlib import Path
from typing import Any

from platform_plugin_sdk.models import PluginMetadata
from platform_plugin_sdk.plugin import PlatformPlugin
from platform_plugin_sdk.plugin_context import PluginContext


class PluginBuilder:
    """Builds SDK context and plugin instances from manifest metadata."""

    @staticmethod
    def build_context(
        *,
        plugin_id: str,
        version: str,
        name: str = "",
        author: str = "",
        description: str = "",
        permissions: list[str] | None = None,
        workflows: list[str] | None = None,
        config: dict[str, Any] | None = None,
        plugin_path: str | Path | None = None,
        app: Any = None,
    ) -> PluginContext:
        metadata = PluginMetadata(
            plugin_id=plugin_id,
            name=name or plugin_id.title(),
            version=version,
            author=author,
            description=description,
            permissions=list(permissions or []),
            workflows=list(workflows or []),
        )
        ctx = PluginContext(
            plugin_id=plugin_id,
            version=version,
            metadata=metadata,
            config=dict(config or {}),
            plugin_path=str(plugin_path) if plugin_path else None,
        )
        if app is not None:
            ctx.bind_app(app)
        return ctx

    @staticmethod
    async def activate(plugin: PlatformPlugin, ctx: PluginContext) -> PlatformPlugin:
        plugin.configure(ctx)
        await plugin.initialize()
        return plugin


def build_plugin_context(record: Any, app: Any = None) -> PluginContext:
    """Build SDK context from a platform_plugins PluginRecord."""
    manifest = record.manifest
    return PluginBuilder.build_context(
        plugin_id=manifest.id,
        version=manifest.version,
        name=manifest.name,
        author=manifest.author,
        description=manifest.description,
        permissions=manifest.permissions,
        workflows=manifest.workflows,
        config=manifest.configuration,
        plugin_path=record.path,
        app=app,
    )
