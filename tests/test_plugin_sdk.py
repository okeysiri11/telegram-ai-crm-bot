"""Tests — Platform Plugin SDK."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from events.event_bus import reset_subscribers
from platform_plugin_sdk import PlatformPlugin, PluginContext
from platform_plugin_sdk.models import PluginConfigSchema, PluginHealthResult
from platform_plugin_sdk.plugin_builder import PluginBuilder
from platform_plugin_sdk.plugin_events import PluginEvent, PluginMetric
from platform_plugin_sdk.plugin_hooks import HookName, PluginHookRegistry
from platform_plugin_sdk.plugin_storage import PluginStorage
from platform_plugin_sdk.exceptions import PluginConfigurationError


class DemoPlugin(PlatformPlugin):
    plugin_id = "demo"
    name = "Demo"
    version = "1.0.0"
    installed = False
    enabled = False

    async def on_install(self, ctx: PluginContext) -> None:
        self.installed = True
        ctx.storage.set("installed", True)

    async def on_enable(self, ctx: PluginContext) -> None:
        self.enabled = True

    async def on_disable(self, ctx: PluginContext) -> None:
        self.enabled = False

    async def health(self) -> PluginHealthResult:
        return PluginHealthResult(status="healthy", details={"enabled": self.enabled})


@pytest.fixture
def ctx(tmp_path: Path) -> PluginContext:
    return PluginBuilder.build_context(
        plugin_id="demo",
        version="1.0.0",
        name="Demo",
        config={"greeting": "hello"},
        plugin_path=str(tmp_path / "demo"),
    )


@pytest.fixture(autouse=True)
def _reset_bus():
    reset_subscribers()
    yield
    reset_subscribers()


# ---- Lifecycle ----

@pytest.mark.asyncio
async def test_plugin_lifecycle(ctx: PluginContext):
    plugin = DemoPlugin()
    plugin.configure(ctx)
    await plugin.initialize()
    await plugin.on_install(ctx)
    assert plugin.installed

    await plugin.start()
    assert plugin.enabled

    health = await plugin.health()
    assert health.status == "healthy"

    await plugin.stop()
    assert not plugin.enabled

    await plugin.reload()
    await plugin.shutdown()


# ---- Context isolation ----

def test_storage_isolation(tmp_path: Path):
    a = PluginStorage("alpha", tmp_path / "storage")
    b = PluginStorage("beta", tmp_path / "storage")
    a.set("key", "alpha-value")
    b.set("key", "beta-value")
    assert a.get("key") == "alpha-value"
    assert b.get("key") == "beta-value"


def test_storage_migrations(tmp_path: Path):
    store = PluginStorage("demo", tmp_path / "storage")
    store.register_migration(1, lambda data: {**data, "v1": True})
    store.set("x", 1)
    version = store.migrate(1)
    assert version == 1
    assert store.get("v1") is True


# ---- Configuration ----

def test_configuration_validation(ctx: PluginContext):
    schema = PluginConfigSchema(required=["greeting"], defaults={"greeting": "hello"})
    ctx.configuration.schema = schema
    config = ctx.configuration.load()
    assert config["greeting"] == "hello"


def test_configuration_missing_required(ctx: PluginContext):
    schema = PluginConfigSchema(required=["missing_key"])
    ctx.configuration.schema = schema
    with pytest.raises(PluginConfigurationError):
        ctx.configuration.load()


# ---- Hooks ----

@pytest.mark.asyncio
async def test_hook_dispatch(ctx: PluginContext):
    registry = PluginHookRegistry("demo")
    calls: list[str] = []

    async def handler(c: PluginContext) -> None:
        calls.append("called")

    registry.register(HookName.ON_ENABLE, handler)
    await registry.dispatch(HookName.ON_ENABLE, ctx)
    assert calls == ["called"]


# ---- Events & metrics ----

@pytest.mark.asyncio
async def test_publish_plugin_event(ctx: PluginContext):
    received: list[str] = []

    async def capture(event: SdkPluginBusEvent) -> None:
        received.append(event.plugin_event_type)

    from platform_plugin_sdk.plugin_events import SdkPluginBusEvent
    from events.event_bus import PlatformEventBus

    PlatformEventBus.subscribe(SdkPluginBusEvent, capture)
    await ctx.publish_event("demo.test", {"x": 1})
    await asyncio.sleep(0.02)
    assert received == ["demo.test"]


def test_metrics_namespacing(ctx: PluginContext):
    plugin = DemoPlugin()
    plugin.configure(ctx)
    metric = ctx.metrics.increment("requests", 2.0, source="test")
    assert metric.plugin_id == "demo"
    assert "plugin.demo.requests" in metric.name


# ---- Scheduler namespacing ----

def test_scheduler_namespaces_handlers(ctx: PluginContext):
    async def handler(payload):
        return payload

    full = ctx.jobs.register("task", handler)
    assert full == "plugin.demo.task"
    assert full in ctx.jobs.handlers


# ---- Builder ----

def test_plugin_builder(ctx: PluginContext):
    assert ctx.plugin_id == "demo"
    assert ctx.metadata.name == "Demo"
    assert ctx.get_config("greeting") == "hello"


@pytest.mark.asyncio
async def test_sdk_plugin_loader_integration(tmp_path: Path):
    from platform_plugins.plugin_loader import PluginLoader
    from platform_plugins.models import PluginRecord, PluginState
    from platform_plugins.plugin_manifest import manifest_from_dict

    plugin_dir = tmp_path / "demo"
    plugin_dir.mkdir()
    for sub in ("workflow", "handlers", "services", "routes", "messages", "permissions", "config", "migrations", "assets"):
        (plugin_dir / sub).mkdir()

    (plugin_dir / "plugin.py").write_text(
        '''
from platform_plugin_sdk import PlatformPlugin
from platform_plugin_sdk.models import PluginHealthResult

class DemoPlugin(PlatformPlugin):
    plugin_id = "demo"
    async def health(self):
        return PluginHealthResult(status="healthy")

def create_plugin():
    return DemoPlugin()
'''.strip(),
        encoding="utf-8",
    )

    manifest = manifest_from_dict(
        {
            "id": "demo",
            "name": "Demo",
            "version": "1.0.0",
            "author": "Test",
            "description": "test",
            "platform_version": ">=1.0.0",
            "dependencies": {"required": [], "optional": []},
            "permissions": ["demo.read"],
            "configuration": {},
            "routes": [],
            "workflows": [],
            "entry_point": "plugin:create_plugin",
        }
    )
    record = PluginRecord(manifest=manifest, path=str(plugin_dir), state=PluginState.DISCOVERED)
    loader = PluginLoader(plugins_root=tmp_path)
    sdk_ctx = loader.load_entry(record)
    plugin = loader.get_plugin("demo")
    assert plugin is not None
    assert sdk_ctx.plugin_id == "demo"
    health = await loader.run_health(record, sdk_ctx)
    assert health["status"] == "healthy"
