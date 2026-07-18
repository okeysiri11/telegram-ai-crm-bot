# Plugin lifecycle — install, enable, disable, upgrade, reload, uninstall.

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_plugins.exceptions import (
    PluginDependencyError,
    PluginLifecycleError,
    PluginNotFoundError,
)
from platform_plugins.models import PluginHealth, PluginRecord, PluginState
from platform_plugins.plugin_context import PluginContext
from platform_plugins.plugin_dependencies import check_dependencies, resolve_install_order
from platform_plugins.plugin_events import (
    PluginDisabledEvent,
    PluginEnabledEvent,
    PluginFailedEvent,
    PluginInstalledEvent,
    PluginReloadedEvent,
    PluginRemovedEvent,
    publish_plugin_event,
)
from platform_plugins.plugin_loader import PluginLoader
from platform_plugins.plugin_registry import PluginRegistry
from platform_plugins.plugin_store import PluginStore

logger = logging.getLogger(__name__)


class PluginLifecycle:
    def __init__(
        self,
        registry: PluginRegistry,
        store: PluginStore,
        loader: PluginLoader,
    ) -> None:
        self.registry = registry
        self.store = store
        self.loader = loader
        self._contexts: dict[str, PluginContext] = {}

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _log(self, record: PluginRecord, message: str) -> None:
        record.logs.append(f"{self._now()} {message}")
        logger.info("plugin_lifecycle id=%s %s", record.id, message)

    async def install(self, plugin_id: str, *, app: Any = None) -> PluginRecord:
        record = self.registry.get(plugin_id)
        if record.state in (PluginState.INSTALLED, PluginState.ENABLED, PluginState.DISABLED):
            return record

        missing = check_dependencies(record, self.registry.all())
        if missing:
            raise PluginDependencyError(f"Unmet dependencies: {', '.join(missing)}")

        order = resolve_install_order(plugin_id, self.registry.all())
        for pid in order:
            rec = self.registry.get(pid)
            if rec.state == PluginState.DISCOVERED:
                await self._do_install(rec, app=app)

        return self.registry.get(plugin_id)

    async def _do_install(self, record: PluginRecord, *, app: Any = None) -> None:
        try:
            hook = self.loader.get_hook(record.id, "on_install")
            if hook:
                ctx = self._context_for(record, app)
                result = hook(ctx)
                if hasattr(result, "__await__"):
                    await result

            record.state = PluginState.INSTALLED
            record.installed_at = self._now()
            record.last_error = None
            self.store.mark_installed(record)
            self._log(record, "installed")
            await publish_plugin_event(
                PluginInstalledEvent(
                    event_id=f"plugin-installed-{record.id}",
                    plugin_id=record.id,
                    version=record.manifest.version,
                    message="Plugin installed",
                )
            )
        except Exception as exc:
            record.state = PluginState.FAILED
            record.last_error = str(exc)
            await self._fail(record, str(exc))
            raise PluginLifecycleError(str(exc)) from exc

    async def enable(self, plugin_id: str, *, app: Any = None) -> PluginRecord:
        record = self.registry.get(plugin_id)
        if record.state == PluginState.DISCOVERED:
            await self.install(plugin_id, app=app)
            record = self.registry.get(plugin_id)

        if record.state == PluginState.ENABLED:
            return record

        if record.state not in (PluginState.INSTALLED, PluginState.DISABLED, PluginState.FAILED):
            raise PluginLifecycleError(f"Cannot enable plugin in state {record.state.value}")

        try:
            ctx = self.loader.load_entry(record, app=app)
            self._contexts[plugin_id] = ctx

            hook = self.loader.get_hook(plugin_id, "on_enable")
            if hook:
                result = hook(ctx)
                if hasattr(result, "__await__"):
                    await result

            record.state = PluginState.ENABLED
            record.enabled_at = self._now()
            record.disabled_at = None
            record.last_error = None
            self.store.mark_enabled(plugin_id)
            self._log(record, "enabled")
            await publish_plugin_event(
                PluginEnabledEvent(
                    event_id=f"plugin-enabled-{record.id}",
                    plugin_id=record.id,
                    version=record.manifest.version,
                    message="Plugin enabled",
                )
            )
            return record
        except Exception as exc:
            record.state = PluginState.FAILED
            record.last_error = str(exc)
            await self._fail(record, str(exc))
            raise PluginLifecycleError(str(exc)) from exc

    async def disable(self, plugin_id: str) -> PluginRecord:
        record = self.registry.get(plugin_id)
        if record.state != PluginState.ENABLED:
            if record.state == PluginState.DISABLED:
                return record
            raise PluginLifecycleError(f"Cannot disable plugin in state {record.state.value}")

        try:
            hook = self.loader.get_hook(plugin_id, "on_disable")
            if hook:
                ctx = self._contexts.get(plugin_id) or self._context_for(record)
                result = hook(ctx)
                if hasattr(result, "__await__"):
                    await result

            self.loader.unload(plugin_id)
            self._contexts.pop(plugin_id, None)
            record.loaded = False
            record.state = PluginState.DISABLED
            record.disabled_at = self._now()
            self.store.mark_disabled(plugin_id)
            self._log(record, "disabled")
            await publish_plugin_event(
                PluginDisabledEvent(
                    event_id=f"plugin-disabled-{record.id}",
                    plugin_id=record.id,
                    version=record.manifest.version,
                    message="Plugin disabled",
                )
            )
            return record
        except Exception as exc:
            record.state = PluginState.FAILED
            record.last_error = str(exc)
            await self._fail(record, str(exc))
            raise PluginLifecycleError(str(exc)) from exc

    async def reload(self, plugin_id: str, *, app: Any = None) -> PluginRecord:
        record = self.registry.get(plugin_id)
        was_enabled = record.state == PluginState.ENABLED
        if was_enabled:
            await self.disable(plugin_id)
        self.loader.unload(plugin_id)
        record.loaded = False
        if was_enabled:
            await self.enable(plugin_id, app=app)
        self._log(record, "reloaded")
        await publish_plugin_event(
            PluginReloadedEvent(
                event_id=f"plugin-reloaded-{record.id}",
                plugin_id=record.id,
                version=record.manifest.version,
                message="Plugin reloaded",
            )
        )
        return record

    async def upgrade(self, plugin_id: str, *, app: Any = None) -> PluginRecord:
        record = self.registry.get(plugin_id)
        was_enabled = record.state == PluginState.ENABLED
        if was_enabled:
            await self.disable(plugin_id)

        # Re-read manifest from disk
        from platform_plugins.plugin_manifest import load_manifest
        from platform_plugins.plugin_validator import validate_manifest

        manifest = load_manifest(Path(record.path) / "manifest.yaml")  # type: ignore[name-defined]
        validate_manifest(manifest)
        record.manifest = manifest
        record.loaded = False
        self._log(record, f"upgraded to {manifest.version}")

        if was_enabled:
            await self.enable(plugin_id, app=app)
        return record

    async def uninstall(self, plugin_id: str) -> PluginRecord:
        record = self.registry.get(plugin_id)
        if record.state == PluginState.ENABLED:
            await self.disable(plugin_id)

        try:
            hook = self.loader.get_hook(plugin_id, "on_uninstall")
            if hook:
                ctx = self._context_for(record)
                result = hook(ctx)
                if hasattr(result, "__await__"):
                    await result
        except Exception as exc:
            logger.warning("plugin_uninstall_hook_failed id=%s error=%s", plugin_id, exc)

        self.loader.unload(plugin_id)
        self._contexts.pop(plugin_id, None)
        record.state = PluginState.UNINSTALLED
        record.loaded = False
        self.store.mark_uninstalled(plugin_id)
        self._log(record, "uninstalled")
        await publish_plugin_event(
            PluginRemovedEvent(
                event_id=f"plugin-removed-{record.id}",
                plugin_id=record.id,
                version=record.manifest.version,
                message="Plugin uninstalled",
            )
        )
        return record

    async def health_check(self, plugin_id: str) -> PluginHealth:
        record = self.registry.get(plugin_id)
        ctx = self._contexts.get(plugin_id) or self._context_for(record)
        try:
            details = await self.loader.run_health(record, ctx)
            status = str(details.get("status", "healthy"))
            health = PluginHealth(
                plugin_id=plugin_id,
                status=status,
                message=str(details.get("message", "")),
                details=details,
            )
        except Exception as exc:
            health = PluginHealth(
                plugin_id=plugin_id,
                status="unhealthy",
                message=str(exc),
            )
        record.health = health
        return health

    async def _fail(self, record: PluginRecord, error: str) -> None:
        await publish_plugin_event(
            PluginFailedEvent(
                event_id=f"plugin-failed-{record.id}",
                plugin_id=record.id,
                version=record.manifest.version,
                message="Plugin operation failed",
                error=error,
            )
        )

    def _context_for(self, record: PluginRecord, app: Any = None) -> PluginContext:
        ctx = PluginContext(
            plugin_id=record.id,
            plugin_version=record.manifest.version,
            config=dict(record.manifest.configuration),
        )
        if app is not None:
            ctx.bind_app(app)
        return ctx

