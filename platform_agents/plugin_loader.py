# Agent plugin discovery and loading from platform_plugins/.

from __future__ import annotations

import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Type

from platform_agents.base_agent import BaseAgent
from platform_agents.exceptions import AgentPluginLoadError
from platform_agents.registry import AgentRegistry
from platform_agents.validation import validate_plugin_manifest

logger = logging.getLogger(__name__)

DEFAULT_AGENT_PLUGINS_ROOT = Path(__file__).resolve().parent.parent / "platform_plugins"


class AgentPluginLoader:
    """Discover and register agent plugins from platform_plugins/<name>/."""

    def __init__(self, plugins_root: Path | None = None) -> None:
        self.plugins_root = plugins_root or DEFAULT_AGENT_PLUGINS_ROOT

    def discover(self) -> list[Path]:
        """Return plugin directories containing plugin.json and agent.py."""
        found: list[Path] = []
        if not self.plugins_root.is_dir():
            logger.warning("agent_plugins_root_missing path=%s", self.plugins_root)
            return found

        for entry in sorted(self.plugins_root.iterdir()):
            if not entry.is_dir() or entry.name.startswith((".", "_")):
                continue
            manifest = entry / "plugin.json"
            agent_module = entry / "agent.py"
            if manifest.is_file() and agent_module.is_file():
                found.append(entry)
                logger.info("agent_plugin_discovered path=%s", entry.name)
        return found

    def load_plugin(self, plugin_dir: Path) -> Type[BaseAgent]:
        manifest_path = plugin_dir / "plugin.json"
        agent_path = plugin_dir / "agent.py"

        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AgentPluginLoadError(str(plugin_dir), f"invalid plugin.json: {exc}") from exc

        meta = validate_plugin_manifest(raw)
        entry_point = raw.get("entry_point", "agent:Agent")

        agent_cls = self._import_agent_class(plugin_dir, agent_path, entry_point)

        class_meta = agent_cls.metadata()
        if class_meta.id != meta.id:
            raise AgentPluginLoadError(
                str(plugin_dir),
                f"plugin.json id '{meta.id}' does not match agent class id '{class_meta.id}'",
            )

        return agent_cls

    def load_and_register(self, registry: AgentRegistry, plugin_dir: Path | None = None) -> list[str]:
        """Discover all plugins (or load one) and register them."""
        registered: list[str] = []
        dirs = [plugin_dir] if plugin_dir else self.discover()

        for directory in dirs:
            try:
                agent_cls = self.load_plugin(directory)
                meta = registry.register(agent_cls, source="plugin")
                registered.append(meta.id)
            except Exception as exc:
                logger.warning("agent_plugin_load_failed path=%s error=%s", directory, exc)
                if plugin_dir is not None:
                    raise
        return registered

    def _import_agent_class(
        self,
        plugin_dir: Path,
        agent_path: Path,
        entry_point: str,
    ) -> Type[BaseAgent]:
        module_name = f"platform_agent_plugin_{plugin_dir.name}"
        spec = importlib.util.spec_from_file_location(module_name, agent_path)
        if spec is None or spec.loader is None:
            raise AgentPluginLoadError(str(plugin_dir), "failed to create module spec for agent.py")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        if ":" not in entry_point:
            raise AgentPluginLoadError(str(plugin_dir), f"invalid entry_point '{entry_point}'")

        symbol_name = entry_point.split(":", 1)[1]
        if not hasattr(module, symbol_name):
            raise AgentPluginLoadError(str(plugin_dir), f"entry point '{symbol_name}' not found in agent.py")

        agent_cls = getattr(module, symbol_name)
        if not isinstance(agent_cls, type) or not issubclass(agent_cls, BaseAgent):
            raise AgentPluginLoadError(str(plugin_dir), f"{symbol_name} must be a BaseAgent subclass")

        return agent_cls


agent_plugin_loader = AgentPluginLoader()
