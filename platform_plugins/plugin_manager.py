# Plugin manager — central orchestrator for the plugin system.

from __future__ import annotations

import logging
from typing import Any

from platform_plugins.models import PluginRecord, PluginState
from platform_plugins.plugin_dependencies import dependency_graph_payload
from platform_plugins.plugin_lifecycle import PluginLifecycle
from platform_plugins.plugin_loader import plugin_loader
from platform_plugins.plugin_manifest import manifest_schema
from platform_plugins.plugin_registry import plugin_registry
from platform_plugins.plugin_store import plugin_store

logger = logging.getLogger(__name__)


class PluginManager:
    """Platform Core plugin orchestrator — domain-agnostic."""

    def __init__(self) -> None:
        self.registry = plugin_registry
        self.store = plugin_store
        self.loader = plugin_loader
        self.lifecycle = PluginLifecycle(self.registry, self.store, self.loader)
        self._initialized = False
        self._app: Any = None

    def reset(self) -> None:
        self.registry.clear()
        self._initialized = False
        self._app = None

    async def initialize(self, *, app: Any = None, auto_enable: bool = True) -> dict[str, Any]:
        """Discover plugins, restore persisted state, optionally auto-enable."""
        if app is not None:
            self._app = app

        self.store.load()
        discovered = self.loader.discover()
        for record in discovered:
            self.registry.register(record)

        self.store.apply_persisted_state(self.registry.all())

        if auto_enable:
            for plugin_id in self.store.enabled_ids():
                record = self.registry.get_optional(plugin_id)
                if record and record.state == PluginState.ENABLED:
                    try:
                        await self.lifecycle.enable(plugin_id, app=self._app)
                    except Exception as exc:
                        logger.warning("plugin_auto_enable_failed id=%s error=%s", plugin_id, exc)

        self._initialized = True
        return await self.status()

    async def status(self) -> dict[str, Any]:
        records = self.registry.all()
        installed = [r.to_dict() for r in records.values() if r.state != PluginState.DISCOVERED]
        enabled = [r.id for r in records.values() if r.state == PluginState.ENABLED]
        disabled = [r.id for r in records.values() if r.state == PluginState.DISABLED]
        failed = [r.id for r in records.values() if r.state == PluginState.FAILED]
        discovered = [r.id for r in records.values() if r.state == PluginState.DISCOVERED]

        return {
            "initialized": self._initialized,
            "discovered": discovered,
            "installed": installed,
            "enabled": enabled,
            "disabled": disabled,
            "failed": failed,
            "count": {
                "discovered": len(discovered),
                "installed": len(installed),
                "enabled": len(enabled),
                "disabled": len(disabled),
                "failed": len(failed),
            },
        }

    async def list_plugins(self) -> dict[str, Any]:
        status = await self.status()
        status["plugins"] = [r.to_dict() for r in self.registry.all().values()]
        return status

    async def get_plugin(self, plugin_id: str) -> dict[str, Any]:
        return self.registry.get(plugin_id).to_dict()

    async def install(self, plugin_id: str) -> dict[str, Any]:
        record = await self.lifecycle.install(plugin_id, app=self._app)
        return record.to_dict()

    async def enable(self, plugin_id: str) -> dict[str, Any]:
        record = await self.lifecycle.enable(plugin_id, app=self._app)
        return record.to_dict()

    async def disable(self, plugin_id: str) -> dict[str, Any]:
        record = await self.lifecycle.disable(plugin_id)
        return record.to_dict()

    async def reload(self, plugin_id: str | None = None) -> dict[str, Any]:
        if plugin_id:
            record = await self.lifecycle.reload(plugin_id, app=self._app)
            return {"reloaded": 1, "plugin": record.to_dict()}

        reloaded = 0
        results = []
        for record in self.registry.list_by_state(PluginState.ENABLED):
            try:
                updated = await self.lifecycle.reload(record.id, app=self._app)
                results.append(updated.to_dict())
                reloaded += 1
            except Exception as exc:
                results.append({"id": record.id, "error": str(exc)})
        return {"reloaded": reloaded, "plugins": results}

    async def upgrade(self, plugin_id: str) -> dict[str, Any]:
        record = await self.lifecycle.upgrade(plugin_id, app=self._app)
        return record.to_dict()

    async def uninstall(self, plugin_id: str) -> dict[str, Any]:
        record = await self.lifecycle.uninstall(plugin_id)
        return record.to_dict()

    async def health(self, plugin_id: str | None = None) -> dict[str, Any]:
        if plugin_id:
            health = await self.lifecycle.health_check(plugin_id)
            return health.to_dict()

        checks = []
        for record in self.registry.all().values():
            if record.state in (PluginState.ENABLED, PluginState.INSTALLED):
                health = await self.lifecycle.health_check(record.id)
                checks.append(health.to_dict())
        healthy = sum(1 for c in checks if c["status"] == "healthy")
        return {
            "overall": "healthy" if healthy == len(checks) else "degraded",
            "checks": checks,
            "healthy": healthy,
            "total": len(checks),
        }

    async def dependencies(self) -> dict[str, Any]:
        return dependency_graph_payload(self.registry.all())

    def manifest_schema(self) -> dict[str, Any]:
        return manifest_schema()


plugin_manager = PluginManager()
