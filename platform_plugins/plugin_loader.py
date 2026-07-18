# Plugin discovery and lazy loading.

from __future__ import annotations

import importlib.util
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from platform_plugins.exceptions import PluginLoadError, PluginNotFoundError
from platform_plugins.models import PluginRecord, PluginState
from platform_plugins.plugin_context import PluginContext
from platform_plugins.plugin_manifest import load_manifest
from platform_plugins.plugin_validator import (
    validate_manifest,
    validate_platform_version,
    validate_plugin_directory,
)
from platform_plugins.plugin_context import PLATFORM_VERSION

logger = logging.getLogger(__name__)

DEFAULT_PLUGINS_ROOT = Path(__file__).resolve().parent.parent / "plugins"


class PluginLoader:
    """Discovers plugin folders and lazily loads entry points."""

    def __init__(self, plugins_root: Path | None = None) -> None:
        self.plugins_root = plugins_root or DEFAULT_PLUGINS_ROOT
        self._loaded_modules: dict[str, Any] = {}
        self._hooks: dict[str, dict[str, Callable[..., Any]]] = {}

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
                record = PluginRecord(
                    manifest=manifest,
                    path=str(entry),
                    state=PluginState.DISCOVERED,
                )
                records.append(record)
                logger.info("plugin_discovered id=%s version=%s", manifest.id, manifest.version)
            except Exception as exc:
                logger.warning("plugin_discover_failed path=%s error=%s", entry, exc)
        return records

    def load_entry(self, record: PluginRecord, app: Any = None) -> PluginContext:
        """Lazy-load plugin entry point and return context."""
        ctx = PluginContext(
            plugin_id=record.id,
            plugin_version=record.manifest.version,
            config=dict(record.manifest.configuration),
        )
        if app is not None:
            ctx.bind_app(app)

        entry = record.manifest.entry_point
        if not entry:
            record.loaded = True
            return ctx

        module_path, _, callable_name = entry.partition(":")
        if not callable_name:
            raise PluginLoadError(f"Invalid entry_point for {record.id}: {entry}")

        plugin_root = Path(record.path)
        spec_path = plugin_root / f"{module_path.replace('.', '/')}.py"
        if not spec_path.is_file():
            raise PluginLoadError(f"Entry module not found: {spec_path}")

        mod_name = f"plugin_{record.id}_{module_path.replace('.', '_')}"
        if mod_name in self._loaded_modules:
            mod = self._loaded_modules[mod_name]
        else:
            spec = importlib.util.spec_from_file_location(mod_name, spec_path)
            if spec is None or spec.loader is None:
                raise PluginLoadError(f"Cannot load module: {spec_path}")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self._loaded_modules[mod_name] = mod

        register_fn = getattr(mod, callable_name, None)
        if register_fn is None:
            raise PluginLoadError(f"Callable {callable_name} not found in {entry}")

        hooks: dict[str, Callable[..., Any]] = {"register": register_fn}
        for hook_name in ("on_enable", "on_disable", "on_install", "on_uninstall", "health"):
            fn = getattr(mod, hook_name, None)
            if callable(fn):
                hooks[hook_name] = fn

        self._hooks[record.id] = hooks

        result = register_fn(ctx)
        if hasattr(result, "__await__"):
            raise PluginLoadError("register() must be sync; use on_enable for async setup")

        record.loaded = True
        record.logs.append(f"{_ts()} entry loaded: {entry}")
        return ctx

    def unload(self, plugin_id: str) -> None:
        self._hooks.pop(plugin_id, None)
        to_remove = [k for k in self._loaded_modules if k.startswith(f"plugin_{plugin_id}_")]
        for key in to_remove:
            self._loaded_modules.pop(key, None)

    def get_hook(self, plugin_id: str, name: str) -> Callable[..., Any] | None:
        return self._hooks.get(plugin_id, {}).get(name)

    async def run_health(self, record: PluginRecord, ctx: PluginContext) -> dict[str, Any]:
        health_fn = self.get_hook(record.id, "health")
        if health_fn is None:
            return {"status": "healthy", "message": "No health hook defined"}
        result = health_fn(ctx)
        if hasattr(result, "__await__"):
            result = await result
        if not isinstance(result, dict):
            return {"status": "healthy", "message": str(result)}
        return result


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


plugin_loader = PluginLoader()
