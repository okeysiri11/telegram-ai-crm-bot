"""Tests — Platform Plugin System."""

from __future__ import annotations

import asyncio
import textwrap
from pathlib import Path

import pytest
import yaml
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from events.event_bus import reset_subscribers, subscribe
from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole
from platform_plugins.models import PluginState
from platform_plugins.plugin_dependencies import detect_cycles, resolve_install_order, version_satisfies
from platform_plugins.plugin_events import PluginEnabledEvent, PluginInstalledEvent
from platform_plugins.plugin_loader import PluginLoader
from platform_plugins.plugin_manager import PluginManager
from platform_plugins.plugin_registry import PluginRegistry
from platform_plugins.plugin_store import PluginStore
from platform_plugins.plugins_router import register_plugins_routes


@pytest.fixture
def plugins_root(tmp_path: Path) -> Path:
    root = tmp_path / "plugins"
    root.mkdir()
    return root


def _write_plugin(root: Path, spec: dict) -> Path:
    plugin_dir = root / spec["id"]
    plugin_dir.mkdir()
    for sub in ("workflow", "handlers", "services", "routes", "messages", "permissions", "config", "migrations", "assets"):
        (plugin_dir / sub).mkdir()
    manifest = {
        "id": spec["id"],
        "name": spec.get("name", spec["id"].title()),
        "version": spec.get("version", "1.0.0"),
        "author": "Test",
        "description": spec.get("description", "Test plugin"),
        "platform_version": ">=1.0.0",
        "dependencies": spec.get("dependencies", {"required": [], "optional": []}),
        "permissions": spec.get("permissions", [f"{spec['id']}.read"]),
        "configuration": spec.get("configuration", {}),
        "routes": spec.get("routes", []),
        "workflows": spec.get("workflows", []),
        "entry_point": "plugin:register",
    }
    (plugin_dir / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
    (plugin_dir / "plugin.py").write_text(
        textwrap.dedent(
            f'''
            def register(ctx):
                return {{"plugin_id": ctx.plugin_id}}

            async def health(ctx):
                return {{"status": "healthy", "domain": "{spec["id"]}"}}
            '''
        ).strip(),
        encoding="utf-8",
    )
    return plugin_dir


@pytest.fixture
def manager(plugins_root: Path, tmp_path: Path) -> PluginManager:
    mgr = PluginManager()
    mgr.reset()
    mgr.loader = PluginLoader(plugins_root)
    mgr.store = PluginStore(tmp_path / "store.json")
    mgr.lifecycle = mgr.lifecycle.__class__(mgr.registry, mgr.store, mgr.loader)
    return mgr


@pytest.fixture
def actor_header():
    return {"X-Actor-Telegram-Id": "42"}


@pytest.fixture(autouse=True)
def _grant_plugins_permissions(monkeypatch):
    async def _owner(_tid):
        return ManagementRole.OWNER

    async def _authorize(_principal, _permission):
        return True

    async def _authenticate(_tid):
        return _principal_mock()

    def _principal_mock():
        from platform_identity.models import AuthMethod, Principal, PlatformRole

        return Principal(
            principal_id="test",
            auth_method=AuthMethod.TELEGRAM_USER,
            telegram_id=42,
            roles=[PlatformRole.OWNER.value],
        )

    monkeypatch.setattr("platform_management.permissions.resolve_role", _owner)
    from platform_identity.identity_service import identity_service

    monkeypatch.setattr(identity_service, "authorize", _authorize)
    monkeypatch.setattr(identity_service, "authenticate_telegram", _authenticate)


@pytest.fixture(autouse=True)
def _reset_events():
    reset_subscribers()
    yield
    reset_subscribers()


# ---- Discovery & registration ----

@pytest.mark.asyncio
async def test_discover_plugins(manager: PluginManager, plugins_root: Path):
    _write_plugin(plugins_root, {"id": "alpha"})
    _write_plugin(plugins_root, {"id": "beta"})

    status = await manager.initialize(auto_enable=False)
    assert status["count"]["discovered"] == 2
    assert set(status["discovered"]) == {"alpha", "beta"}


@pytest.mark.asyncio
async def test_manifest_validation_rejects_bad_id(manager: PluginManager, plugins_root: Path):
    plugin_dir = plugins_root / "bad"
    plugin_dir.mkdir()
    for sub in ("workflow", "handlers", "services", "routes", "messages", "permissions", "config", "migrations", "assets"):
        (plugin_dir / sub).mkdir()
    (plugin_dir / "manifest.yaml").write_text(
        yaml.dump(
            {
                "id": "Bad-ID",
                "name": "Bad",
                "version": "1.0.0",
                "author": "Test",
                "description": "bad",
                "platform_version": ">=1.0.0",
                "dependencies": {"required": [], "optional": []},
                "permissions": [],
                "configuration": {},
                "routes": [],
                "workflows": [],
            }
        ),
        encoding="utf-8",
    )
    status = await manager.initialize(auto_enable=False)
    assert status["count"]["discovered"] == 0


# ---- Dependencies ----

def test_version_constraints():
    assert version_satisfies("1.2.0", ">=1.0.0")
    assert not version_satisfies("0.9.0", ">=1.0.0")
    assert version_satisfies("1.2.3", "1.2.3")


def test_cycle_detection():
    graph = {"a": ["b"], "b": ["c"], "c": ["a"]}
    cycle = detect_cycles(graph)
    assert cycle


@pytest.mark.asyncio
async def test_install_requires_dependencies(manager: PluginManager, plugins_root: Path):
    _write_plugin(
        plugins_root,
        {
            "id": "construction",
            "dependencies": {"required": [{"id": "legal", "version": ">=1.0.0"}], "optional": []},
        },
    )
    _write_plugin(plugins_root, {"id": "legal"})
    await manager.initialize(auto_enable=False)

    record = await manager.install("construction")
    assert record["state"] == PluginState.INSTALLED.value
    legal = manager.registry.get("legal")
    assert legal.state == PluginState.INSTALLED


# ---- Lifecycle ----

@pytest.mark.asyncio
async def test_full_lifecycle(manager: PluginManager, plugins_root: Path):
    events: list[str] = []

    async def _capture(event):
        events.append(event.event_type)

    subscribe(PluginInstalledEvent, _capture)
    subscribe(PluginEnabledEvent, _capture)

    _write_plugin(plugins_root, {"id": "auto"})
    await manager.initialize(auto_enable=False)

    installed = await manager.install("auto")
    assert installed["state"] == PluginState.INSTALLED.value

    enabled = await manager.enable("auto")
    assert enabled["state"] == PluginState.ENABLED.value
    assert enabled["loaded"] is True

    health = await manager.health("auto")
    assert health["status"] == "healthy"

    reloaded = await manager.reload("auto")
    assert reloaded["plugin"]["state"] == PluginState.ENABLED.value

    disabled = await manager.disable("auto")
    assert disabled["state"] == PluginState.DISABLED.value
    assert disabled["loaded"] is False

    removed = await manager.uninstall("auto")
    assert removed["state"] == PluginState.UNINSTALLED.value
    await asyncio.sleep(0.05)
    assert "PluginInstalledEvent" in events
    assert "PluginEnabledEvent" in events


@pytest.mark.asyncio
async def test_failure_recovery(manager: PluginManager, plugins_root: Path):
    plugin_dir = _write_plugin(plugins_root, {"id": "fail"})
    (plugin_dir / "plugin.py").write_text(
        "def register(ctx):\n    raise RuntimeError('boom')\n",
        encoding="utf-8",
    )
    await manager.initialize(auto_enable=False)
    await manager.install("fail")

    with pytest.raises(Exception):
        await manager.enable("fail")

    record = manager.registry.get("fail")
    assert record.state == PluginState.FAILED
    assert record.last_error


# ---- Permissions via API ----

@pytest.mark.asyncio
async def test_management_api_plugins(actor_header, manager: PluginManager, plugins_root: Path, monkeypatch):
    _write_plugin(plugins_root, {"id": "auto"})
    _write_plugin(plugins_root, {"id": "legal"})

    from platform_plugins import plugin_manager as global_manager

    monkeypatch.setattr(global_manager, "loader", manager.loader)
    monkeypatch.setattr(global_manager, "store", manager.store)
    monkeypatch.setattr(global_manager, "registry", manager.registry)
    monkeypatch.setattr(global_manager, "lifecycle", manager.lifecycle)
    await manager.initialize(auto_enable=False)

    app = web.Application()
    register_management_routes(app)
    register_plugins_routes(app)

    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/management/plugins", headers=actor_header)
        body = await resp.json()
        assert body["success"] is True
        assert body["data"]["count"]["discovered"] == 2

        resp = await client.post("/management/plugins/auto/install", headers=actor_header)
        assert resp.status == 200
        resp = await client.post("/management/plugins/auto/enable", headers=actor_header)
        assert resp.status == 200
        enabled = await resp.json()
        assert enabled["data"]["state"] == "enabled"

        resp = await client.get("/management/plugins/dependencies", headers=actor_header)
        deps = await resp.json()
        assert deps["data"]["valid"] is True

        resp = await client.get("/management/plugins/health", headers=actor_header)
        health = await resp.json()
        assert health["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_resolve_install_order(manager: PluginManager, plugins_root: Path):
    _write_plugin(
        plugins_root,
        {"id": "construction", "dependencies": {"required": [{"id": "legal", "version": ">=1.0.0"}], "optional": []}},
    )
    _write_plugin(plugins_root, {"id": "legal"})
    await manager.initialize(auto_enable=False)
    await manager.install("legal")
    await manager.install("construction")

    order = resolve_install_order("construction", manager.registry.all())
    assert order.index("legal") < order.index("construction")


@pytest.mark.asyncio
async def test_persisted_state(manager: PluginManager, plugins_root: Path, tmp_path: Path):
    _write_plugin(plugins_root, {"id": "auto"})
    await manager.initialize(auto_enable=False)
    await manager.install("auto")
    await manager.enable("auto")

    mgr2 = PluginManager()
    mgr2.reset()
    mgr2.loader = PluginLoader(plugins_root)
    mgr2.store = PluginStore(tmp_path / "store.json")
    mgr2.lifecycle = mgr2.lifecycle.__class__(mgr2.registry, mgr2.store, mgr2.loader)
    await mgr2.initialize(auto_enable=False)

    record = mgr2.registry.get("auto")
    assert record.state in (PluginState.INSTALLED, PluginState.ENABLED)


@pytest.mark.asyncio
async def test_builtin_plugins_discovered():
    from platform_plugins.plugin_manager import plugin_manager

    plugin_manager.reset()
    plugin_manager.loader = PluginLoader(Path(__file__).resolve().parent.parent / "plugins")
    status = await plugin_manager.initialize(auto_enable=False)
    ids = {p["id"] for p in status["installed"]} | set(status["discovered"])
    for expected in ("auto", "realty", "agro", "legal", "insurance", "construction", "medical"):
        assert expected in ids or expected in status["discovered"]
