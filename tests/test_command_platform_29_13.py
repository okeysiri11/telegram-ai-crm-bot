"""Tests — Universal Command Platform (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.command_center.catalogs import (
    COMMAND_CATEGORIES,
    EXECUTION_TYPES,
    UI_SURFACES,
    VOICE_APIS,
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


def test_command_platform_surfaces():
    health = platform_builder.health()
    assert health["universal_command_platform_ready"] is True
    assert health["application_version"] == "1.55.0"

    eng = platform_builder.command_center_os
    execution = eng.execute_command()
    assert set(execution["execution_types"]) == set(EXECUTION_TYPES)

    cats = eng.categories()
    assert set(cats["categories"]) == set(COMMAND_CATEGORIES)

    voice = eng.voice_foundation()
    assert set(voice["apis"]) == set(VOICE_APIS)

    ui = eng.ui_dashboard()
    assert set(ui["surfaces"]) == set(UI_SURFACES)
    assert "Command Palette" in ui["surfaces"]
    assert ui["executes_business_logic"] is False


@pytest.mark.asyncio
async def test_api_command_platform(client):
    palette = await client.post(f"{PREFIX}/command-center/palette", json={"query": "Builder"})
    assert palette.status == 201
    assert len((await palette.json())["results"]) >= 1

    execute = await client.post(
        f"{PREFIX}/command-center/execute",
        json={"command_id": "cmd_open_builder"},
    )
    assert execute.status == 201
    assert (await execute.json())["ok"] is True

    assistant = await client.post(
        f"{PREFIX}/command-center/assistant",
        json={"utterance": "open marketplace"},
    )
    assert assistant.status == 201
    assert (await assistant.json())["ai_command_assistant_ready"] is True

    voice = await client.patch(
        f"{PREFIX}/command-center/voice",
        json={"listening": True, "transcript": "open marketplace"},
    )
    assert voice.status == 200

    hotkeys = await client.get(f"{PREFIX}/command-center/hotkeys")
    assert hotkeys.status == 200

    ui = await client.get(f"{PREFIX}/command-center/ui")
    assert ui.status == 200

    docs = ROOT / "docs" / "UNIVERSAL_COMMAND_PLATFORM.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "commands" / "README.md"
    assert knowledge.exists()
