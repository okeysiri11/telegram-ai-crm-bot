"""Tests — Enterprise Command Center OS (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.command_center.catalogs import (
    COMMAND_CENTER_COMPONENTS,
    WIZARD_STEPS,
)


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


def test_command_center_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.53.0"
    assert health["sprint"] == "32.7"
    assert health["command_center_ready"] is True
    assert health["universal_command_platform_ready"] is True
    assert health["voice_foundation_ready"] is True
    assert health["ai_command_assistant_ready"] is True
    assert health["shortcut_engine_ready"] is True
    assert health["engines"]["command_center"] == "1.0"
    assert health["engines"]["command_registry"] == "1.0"
    assert health["engines"]["command_api"] == "1.0"
    assert health["engines"]["shortcut_engine"] == "1.0"
    assert health["engines"]["voice_api"] == "1.0"
    assert health["command_center_os"]["executes_business_logic"] is False

    catalog = platform_builder.command_center_os.catalog()
    assert catalog["operational"] is True
    assert catalog["orchestrates_user_interaction_only"] is True
    assert catalog["keyboard_first"] is True
    assert catalog["voice_ready"] is True
    assert catalog["ai_native"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["components"]) == set(COMMAND_CENTER_COMPONENTS)


def test_command_center_flow_and_create():
    eng = platform_builder.command_center_os
    overview = eng.engine_overview()
    assert "Command Dispatcher" in overview["components"]

    palette = eng.command_palette("AI")
    assert palette["ready"] is True
    assert any("AI" in r["title"] or "AI" in r["category"] for r in palette["results"])

    executed = eng.execute_command("cmd_open_ops")
    assert executed["ok"] is True
    assert executed["execution"]["executes_business_logic"] is False

    cats = eng.categories()
    assert "Navigation" in cats["categories"]

    voice = eng.voice_foundation({"listening": True, "transcript": "open ops"})
    assert voice["voice_foundation_ready"] is True

    hotkeys = eng.hotkey_engine({"profile": "power"})
    assert hotkeys["profile"] == "power"

    history = eng.command_history(action="favorite", command_id="cmd_open_ops")
    assert "cmd_open_ops" in history["favorites"]

    assistant = eng.ai_assistant(utterance="open analytics")
    assert assistant["ai_command_assistant_ready"] is True

    perf = eng.performance(action="warm_cache")
    assert perf["cache"]["entries"] >= 1

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["command_center"]["command_center_id"]
    assert created["command_registry"]["command_registry_id"]
    assert created["command_api"]["command_api_id"]
    assert created["shortcut_engine"]["shortcut_engine_id"]
    assert created["voice_api"]["voice_api_id"]


@pytest.mark.asyncio
async def test_api_command_center(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.53.0"
    assert body["command_center_ready"] is True

    catalog = await client.get(f"{PREFIX}/command-center/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["executes_business_logic"] is False

    session = await client.post(f"{PREFIX}/command-center/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/command-center/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = (
        ROOT / "src" / "web" / "platform-builder" / "command-center" / "CommandCenterStudio.tsx"
    )
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "CommandCenterOSPage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "COMMAND_CENTER_OS.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "command_center" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.53.0"' in manifest
    assert "32.7" in manifest
