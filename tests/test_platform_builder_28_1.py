"""Tests — Platform Builder Core (Sprint 28.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.catalog import AI_BUILDER_STEPS, BUILDERS, FRAMEWORK_PHASES
from applications.platform_builder.god_mode import GOD_CAPABILITIES, PLATFORM_OWNER_ROLE
from applications.platform_builder.shared.exceptions import ForbiddenError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/platform-builder/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_platform_builder_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    yield
    platform_builder.reset()


def test_version_platform_builder_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.66.0"
    assert health["sprint"] == "34.0"
    assert health["platform_builder_ready"] is True
    assert health["builder_framework_ready"] is True
    assert health["builder_academy_ready"] is True
    assert health["god_mode_ready"] is True
    assert health["builder_navigation_ready"] is True
    assert health["dark_theme_ready"] is True
    assert health["engines"]["builder_engine"] == "1.0"
    assert "step" in FRAMEWORK_PHASES
    assert "create" in FRAMEWORK_PHASES
    assert "Number of AI Agents" in AI_BUILDER_STEPS
    assert PLATFORM_OWNER_ROLE == "platform_owner"
    assert "edit_any_object" in GOD_CAPABILITIES


def test_framework_academy_menu_god_mode():
    boot = platform_builder.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["builder_engine_ready"] is True
    assert boot["web_path_exists"] is True
    assert boot["dashboard_page_exists"] is True
    assert boot["framework_exists"] is True

    builders = platform_builder.engine.list_builders()
    assert builders["count"] >= 14
    assert builders["framework_phases"] == list(FRAMEWORK_PHASES)

    ai = platform_builder.engine.describe("ai")
    assert ai["frame_only"] is False
    assert len(ai["steps"]) == 10
    assert ai["steps"][0]["title"] == "Number of AI Agents"
    assert ai["framework"]["inherited"] is True
    help_item = ai["steps"][0]["help"]
    assert "purpose" in help_item
    assert "benefits" in help_item
    assert "Possible errors" not in help_item["detailed_explanation"]

    concierge = platform_builder.engine.describe("concierge")
    assert concierge["builder"]["constraints"]["one_per_organization"] is True
    assert concierge["builder"]["constraints"]["separate_from_ai_agents"] is True

    preview = platform_builder.engine.preview("crm", {"scope": "demo"})
    assert preview["frame_only"] is True
    created = platform_builder.engine.create("crm", {"scope": "demo"})
    assert created["status"] == "draft_frame"

    academy = platform_builder.academy.set_mode("guided_learning")
    assert academy["ok"] is True
    assert academy["explains_every_screen"] is True
    guide = platform_builder.academy.screen_guide("ai", "Profession")
    assert guide["guided"] is True
    toggle = platform_builder.academy.toggle_learning("ai", False)
    assert toggle["learning_enabled"] is False

    menu_builder = platform_builder.menu("builder")
    assert menu_builder["god_mode_visible"] is False
    assert all(i["id"] != "god_mode" for i in menu_builder["items"])

    menu_owner = platform_builder.menu("platform_owner")
    assert menu_owner["god_mode_visible"] is True
    assert any(i["id"] == "god_mode" for i in menu_owner["items"])

    with pytest.raises(ForbiddenError):
        platform_builder.god_mode.status("builder")

    god = platform_builder.god_mode.status("platform_owner")
    assert god["isolated"] is True
    assert set(GOD_CAPABILITIES).issubset(set(god["capabilities"]))
    action = platform_builder.god_mode.action(
        "platform_owner",
        action="system_diagnostics",
        target="platform",
    )
    assert action["ok"] is True

    roles = platform_builder.roles()
    assert any(r["id"] == "platform_owner" for r in roles["roles"])

    ids = {b["id"] for b in BUILDERS}
    for required in (
        "vertical",
        "ai",
        "concierge",
        "crm",
        "erp",
        "workflow",
        "knowledge",
        "automation",
        "dashboard_builder",
        "template",
        "marketplace",
        "academy",
        "god_mode",
    ):
        assert required in ids


@pytest.mark.asyncio
async def test_api_platform_builder(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.66.0"
    assert body["platform_builder_ready"] is True

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201

    inv = await client.get(f"{PREFIX}/inventory")
    assert inv.status == 200

    dash = await client.get(f"{PREFIX}/dashboard")
    assert dash.status == 200

    builders = await client.get(f"{PREFIX}/builders")
    assert builders.status == 200
    assert (await builders.json())["count"] >= 14

    ai = await client.get(f"{PREFIX}/builders/ai")
    assert ai.status == 200
    assert len((await ai.json())["steps"]) == 10

    prev = await client.post(f"{PREFIX}/builders/ai/preview", json={"payload": {"agents": 3}})
    assert prev.status == 200

    create = await client.post(f"{PREFIX}/builders/vertical/create", json={})
    assert create.status == 201

    academy = await client.post(f"{PREFIX}/academy", json={"mode": "quick_start"})
    assert academy.status == 200

    menu = await client.get(f"{PREFIX}/menu")
    assert menu.status == 200
    assert (await menu.json())["god_mode_visible"] is False

    denied = await client.get(f"{PREFIX}/god-mode")
    assert denied.status == 403

    owner_headers = {"X-Platform-Role": "platform_owner"}
    god = await client.get(f"{PREFIX}/god-mode", headers=owner_headers)
    assert god.status == 200
    assert (await god.json())["ready"] is True

    act = await client.post(
        f"{PREFIX}/god-mode/action",
        json={"action": "architecture_management", "target": "builders"},
        headers=owner_headers,
    )
    assert act.status == 200

    owner_menu = await client.get(f"{PREFIX}/menu", headers=owner_headers)
    assert (await owner_menu.json())["god_mode_visible"] is True


def test_docs_and_web_module_28_1():
    assert (ROOT / "docs" / "PLATFORM_BUILDER_CORE.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "README.md").exists()
    assert (ROOT / "applications" / "platform_builder" / "application.py").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "pages" / "PlatformBuilderDashboard.tsx").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "framework" / "BuilderFramework.tsx").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "pages" / "GodModePage.tsx").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "pages" / "AIBuilderPage.tsx").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "pages" / "ConciergeBuilderPage.tsx").exists()

    docs = (ROOT / "docs" / "PLATFORM_BUILDER_CORE.md").read_text()
    for key in ("Builder Framework", "Builder Academy", "God Mode", "Platform Owner"):
        assert key in docs

    server = (ROOT / "api" / "server.py").read_text()
    assert "register_platform_builder_routes" in server

    menu = (ROOT / "src" / "web" / "navigation" / "managers" / "menuEngine.ts").read_text()
    assert "Platform Builder" in menu
    assert "God Mode" in menu

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.66.0"' in manifest
    assert "33.6" in manifest
