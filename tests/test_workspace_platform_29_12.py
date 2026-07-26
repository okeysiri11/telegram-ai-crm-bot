"""Tests — Unified Workspace Platform (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.workspace_os.catalogs import (
    INTEGRATED_MODULES,
    SEARCH_SCOPES,
    UI_SURFACES,
    WORKSPACE_TYPES,
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


def test_workspace_platform_surfaces():
    health = platform_builder.health()
    assert health["unified_workspace_platform_ready"] is True
    assert health["application_version"] == "1.33.0"

    eng = platform_builder.workspace_os
    types = eng.workspace_types()
    assert set(types["types"]) == set(WORKSPACE_TYPES)

    modules = eng.module_integration()
    assert set(modules["modules"]) == set(INTEGRATED_MODULES)

    ui = eng.ui_dashboard()
    assert set(ui["surfaces"]) == set(UI_SURFACES)
    assert "Workspace Launcher" in ui["surfaces"]
    assert ui["executes_business_logic"] is False

    search = eng.workspace_search("Builder")
    assert set(search["scopes"]) == set(SEARCH_SCOPES)
    assert any(r["title"] == "Builder Studio" for r in search["results"])


@pytest.mark.asyncio
async def test_api_workspace_platform(client):
    types = await client.post(f"{PREFIX}/workspace-os/types", json={"type": "Analytics Workspace"})
    assert types.status == 201
    assert (await types.json())["active_type"] == "Analytics Workspace"

    layout = await client.get(f"{PREFIX}/workspace-os/layout")
    assert layout.status == 200

    session = await client.get(f"{PREFIX}/workspace-os/session")
    assert session.status == 200

    context = await client.patch(
        f"{PREFIX}/workspace-os/context",
        json={"Department Context": "ops"},
    )
    assert context.status == 200
    assert (await context.json())["active_context"]["Department Context"] == "ops"

    multi = await client.post(
        f"{PREFIX}/workspace-os/multitasking",
        json={"action": "clipboard", "clipboard_item": {"kind": "text", "value": "hello"}},
    )
    assert multi.status == 201
    assert len((await multi.json())["clipboard"]) >= 1

    search = await client.get(f"{PREFIX}/workspace-os/search?q=Command")
    assert search.status == 200

    ui = await client.get(f"{PREFIX}/workspace-os/ui")
    assert ui.status == 200

    docs = ROOT / "docs" / "WORKSPACE_PLATFORM.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "workspace" / "README.md"
    assert knowledge.exists()
