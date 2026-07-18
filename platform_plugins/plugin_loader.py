# Plugin discovery and lazy loading via Plugin SDK.

from __future__ import annotations

import importlib.util
import inspect
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from platform_plugin_sdk.plugin import PlatformPlugin
from platform_plugin_sdk.plugin_builder import build_plugin_context
from platform_plugin_sdk.plugin_context import PluginContext
from platform_plugins.exceptions import PluginLoadError
from platform_plugins.models import PluginRecord, PluginState
from platform_plugins.plugin_context import PLATFORM_VERSION
from platform_plugins.plugin_manifest import load_manifest
from platform_plugins.plugin_validator import (
    validate_manifest,
    validate_platform_version,
    validate_plugin_directory,
)

logger = logging.getLogger(__name__)

DEFAULT_PLUGINS_ROOT = Path(__file__).resolve().parent.parent / "plugins"

LEGACY_HOOKS = ("on_enable", "on_disable", "on_install", "on_uninstall", "health", "register")


class PluginLoader:
    """Discovers plugin folders and lazily loads entry points."""

    def __init__(self, plugins_root: Path | None = None) -> None:
        self.plugins_root = plugins_root or DEFAULT_PLUGINS_ROOT
        self._loaded_modules: dict[str, Any] = {}
        self._hooks: dict[str, dict[str, Callable[..., Any]]] = {}
        self._plugins: dict[str, PlatformPlugin] = {}

    def discover(self) -> list[PluginRecord]:
        records: list[PluginRecord] = []
        if not self.plugins_root.is_dir():
            logger.warning("plugins_root_missing path=%s", self.plugins_root)
            return records

        for entry in sorted(self.plugins_root.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            manifest_path = entry / "manifest.yaml"
            if not manifest_path.is_file():
                continue
            try:
                manifest = load_manifest(manifest_path)
                validate_manifest(manifest)
                validate_platform_version(manifest, PLATFORM_VERSION)
                validate_plugin_directory(entry)
                records.append(
                    PluginRecord(manifest=manifest, path=str(entry), state=PluginState.DISCOVERED)
                )
                logger.info("plugin_discovered id=%s version=%s", manifest.id, manifest.version)
            except Exception as exc:
                logger.warning("plugin_discover_failed path=%s error=%s", entry, exc)
        return records

    def load_entry(self, record: PluginRecord, app: Any = None) -> PluginContext:
        ctx = build_plugin_context(record, app=app)
        entry = record.manifest.entry_point
        if not entry:
            record.loaded = True
            return ctx

        mod = self._import_entry_module(record, entry)
        plugin = self._load_platform_plugin(mod, ctx, record)
        if plugin is not None:
            self._register_sdk_health(record.id, plugin)
            record.loaded = True
            record.logs.append(f"{_ts()} SDK plugin loaded: {entry}")
            return ctx

        self._load_legacy_entry(mod, entry, ctx, record)
        record.loaded = True
        record.logs.append(f"{_ts()} legacy entry loaded: {entry}")
        return ctx

    def _import_entry_module(self, record: PluginRecord, entry: str) -> Any:
        module_path, _, callable_name = entry.partition(":")
        if not callable_name:
            raise PluginLoadError(f"Invalid entry_point for {record.id}: {entry}")

        plugin_root = Path(record.path)
        spec_path = plugin_root / f"{module_path.replace('.', '/')}.py"
        if not spec_path.is_file():
            raise PluginLoadError(f"Entry module not found: {spec_path}")

        mod_name = f"plugin_{record.id}_{module_path.replace('.', '_')}"
        if mod_name in self._loaded_modules:
            return self._loaded_modules[mod_name]

        spec = importlib.util.spec_from_file_location(mod_name, spec_path)
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"Cannot load module: {spec_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self._loaded_modules[mod_name] = mod
        return mod

    def _load_platform_plugin(self, mod: Any, ctx: PluginContext, record: PluginRecord) -> PlatformPlugin | None:
        create_fn = getattr(mod, "create_plugin", None)
        if create_fn is None:
            plugin_cls = getattr(mod, "Plugin", None)
            if plugin_cls and inspect.isclass(plugin_cls) and issubclass(plugin_cls, PlatformPlugin):
                create_fn = plugin_cls
            else:
                return None

        instance = create_fn() if inspect.isclass(create_fn) else create_fn()
        if not isinstance(instance, PlatformPlugin):
            raise PluginLoadError(f"create_plugin must return PlatformPlugin for {record.id}")

        if not instance.plugin_id:
            instance.plugin_id = record.id  # type: ignore[misc]

        instance.configure(ctx)
        self._plugins[record.id] = instance
        return instance

    def _register_sdk_health(self, plugin_id: str, plugin: PlatformPlugin) -> None:
        async def _health(_ctx: PluginContext) -> dict[str, Any]:
            result = await plugin.health()
            return result.to_dict()

        self._hooks[plugin_id] = {"health": _health}

    def _load_legacy_entry(self, mod: Any, entry: str, ctx: PluginContext, record: PluginRecord) -> None:
        _, _, callable_name = entry.partition(":")
        register_fn = getattr(mod, callable_name, None)
        if register_fn is None:
            raise PluginLoadError(f"Callable {callable_name} not found in {entry}")

        hooks: dict[str, Callable[..., Any]] = {"register": register_fn}
        for hook_name in LEGACY_HOOKS:
            fn = getattr(mod, hook_name, None)
            if callable(fn):
                hooks[hook_name] = fn

        self._hooks[record.id] = hooks
        result = register_fn(ctx)
        if inspect.isawaitable(result):
            raise PluginLoadError("register() must be sync; use on_enable for async setup")

    def unload(self, plugin_id: str) -> None:
        self._hooks.pop(plugin_id, None)
        self._plugins.pop(plugin_id, None)
        for key in [k for k in self._loaded_modules if k.startswith(f"plugin_{plugin_id}_")]:
            self._loaded_modules.pop(key, None)

    def get_hook(self, plugin_id: str, name: str) -> Callable[..., Any] | None:
        return self._hooks.get(plugin_id, {}).get(name)

    def get_plugin(self, plugin_id: str) -> PlatformPlugin | None:
        return self._plugins.get(plugin_id)

    async def run_health(self, record: PluginRecord, ctx: PluginContext) -> dict[str, Any]:
        plugin = self.get_plugin(record.id)
        if plugin is not None:
            result = await plugin.health()
            return result.to_dict()

        health_fn = self.get_hook(record.id, "health")
        if health_fn is None:
            return {"status": "healthy", "message": "No health hook defined"}
        result = health_fn(ctx)
        if inspect.isawaitable(result):
            result = await result
        if hasattr(result, "to_dict"):
            return result.to_dict()
        if not isinstance(result, dict):
            return {"status": "healthy", "message": str(result)}
        return result


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


plugin_loader = PluginLoader()
