"""Tests — Enterprise Workspace OS (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.workspace_os.catalogs import WORKSPACE_OS_COMPONENTS, WIZARD_STEPS


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


def test_workspace_os_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.51.0"
    assert health["sprint"] == "32.5"
    assert health["workspace_os_ready"] is True
    assert health["workspace_manager_ready"] is True
    assert health["layout_engine_ready"] is True
    assert health["session_manager_ready"] is True
    assert health["context_engine_ready"] is True
    assert health["unified_workspace_platform_ready"] is True
    assert health["engines"]["workspace_os"] == "1.0"
    assert health["engines"]["workspace_registry"] == "1.0"
    assert health["engines"]["layout_engine"] == "1.0"
    assert health["engines"]["context_engine"] == "1.0"
    assert health["engines"]["session_manager"] == "1.0"
    assert health["workspace_os"]["executes_business_logic"] is False

    catalog = platform_builder.workspace_os.catalog()
    assert catalog["operational"] is True
    assert catalog["unified_operating_environment"] is True
    assert catalog["multi_workspace"] is True
    assert catalog["role_aware"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["components"]) == set(WORKSPACE_OS_COMPONENTS)


def test_workspace_os_flow_and_create():
    eng = platform_builder.workspace_os
    overview = eng.engine_overview()
    assert "Workspace Kernel" in overview["components"]

    types = eng.workspace_types("Developer Workspace")
    assert types["active_type"] == "Developer Workspace"

    layout = eng.layout_engine({"split": "ide"})
    assert "Dockable Panels" in layout["features"]
    assert layout["state"]["split"] == "ide"

    session = eng.session_management({"action": "restore", "activity": "opened layout"})
    assert session["session_restore"] is True

    modules = eng.module_integration("Builder Studio")
    assert "Builder Studio" in modules["open_tabs"]

    context = eng.context_engine({"Project Context": "proj_1"})
    assert context["active_context"]["Project Context"] == "proj_1"

    multi = eng.multitasking(action="create_workspace", name="Dev 2", workspace_type="Developer Workspace")
    assert len(multi["workspaces"]) >= 2

    search = eng.workspace_search("AI", "Module Search")
    assert search["ready"] is True

    perf = eng.performance(action="warm_cache")
    assert perf["cache"]["entries"] >= 1

    wiz = eng.start_session()
    eng.update_session(wiz["session_id"], {"step": 10, "draft": {"workspace_type": "Builder Workspace"}})
    created = eng.create(wiz["session_id"])
    assert created["ok"] is True
    assert created["workspace_os"]["workspace_os_id"]
    assert created["workspace_registry"]["workspace_registry_id"]
    assert created["layout_engine"]["layout_engine_id"]
    assert created["context_engine"]["context_engine_id"]
    assert created["session_manager"]["session_manager_id"]


@pytest.mark.asyncio
async def test_api_workspace_os(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.51.0"
    assert body["workspace_os_ready"] is True

    catalog = await client.get(f"{PREFIX}/workspace-os/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["layout_engine_ready"] is True

    session = await client.post(f"{PREFIX}/workspace-os/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/workspace-os/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = ROOT / "src" / "web" / "platform-builder" / "workspace-os" / "WorkspaceOSStudio.tsx"
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "WorkspaceOSPage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "ENTERPRISE_WORKSPACE_OS.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "workspace_os" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.51.0"' in manifest
    assert "32.5" in manifest
