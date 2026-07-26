"""Tests — Enterprise Digital Twin Core (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.digital_twin.catalogs import DIGITAL_TWIN_COMPONENTS, WIZARD_STEPS


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


def test_digital_twin_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.42.0"
    assert health["sprint"] == "32.2"
    assert health["digital_twin_ready"] is True
    assert health["organization_mirror_ready"] is True
    assert health["twin_synchronization_ready"] is True
    assert health["snapshot_engine_ready"] is True
    assert health["engines"]["digital_twin_engine"] == "1.0"
    assert health["engines"]["twin_registry"] == "1.0"
    assert health["engines"]["synchronization_engine"] == "1.0"
    assert health["engines"]["snapshot_engine"] == "1.0"
    assert health["engines"]["twin_api"] == "1.0"
    assert health["digital_twin"]["executes_business_logic"] is False
    assert health["digital_twin"]["owns_business_logic"] is False

    catalog = platform_builder.digital_twin.catalog()
    assert catalog["operational"] is True
    assert catalog["read_only_reflection_layer"] is True
    assert catalog["mirrors_verified_platform_state"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["components"]) == set(DIGITAL_TWIN_COMPONENTS)


def test_digital_twin_flow_and_create():
    eng = platform_builder.digital_twin
    overview = eng.engine_overview()
    assert "Twin Synchronization Engine" in overview["components"]

    org = eng.organization_mirror()
    assert "Organizations" in org["entities"]

    ai = eng.ai_mirror()
    assert ai["read_only"] is True

    workflow = eng.workflow_mirror()
    assert "Critical Paths" in workflow["entities"]

    knowledge = eng.knowledge_mirror()
    assert knowledge["verified_state_only"] is True

    resources = eng.resource_mirror()
    assert "Background Workers" in resources["entities"]

    snap = eng.snapshot_engine(action="capture", snapshot_type="Realtime Snapshot")
    assert snap["created"]["snapshot_id"]

    comparison = eng.state_comparison(dimension="AI Growth")
    assert comparison["selected"] == "AI Growth"

    sync = eng.sync_engine.sync(mode="delta")
    assert sync["ok"] is True

    perf = eng.performance(action="incremental_sync")
    assert perf["cache"]["entries"] >= 1

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["digital_twin_engine"]["digital_twin_engine_id"]
    assert created["twin_registry"]["twin_registry_id"]
    assert created["synchronization_engine"]["synchronization_engine_id"]
    assert created["snapshot_engine"]["snapshot_engine_id"]
    assert created["twin_api"]["twin_api_id"]


@pytest.mark.asyncio
async def test_api_digital_twin(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.42.0"
    assert body["digital_twin_ready"] is True

    catalog = await client.get(f"{PREFIX}/digital-twin/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["owns_business_logic"] is False

    session = await client.post(f"{PREFIX}/digital-twin/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/digital-twin/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = ROOT / "src" / "web" / "platform-builder" / "digital-twin" / "DigitalTwinStudio.tsx"
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "DigitalTwinPage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "ENTERPRISE_DIGITAL_TWIN.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "digital_twin" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.42.0"' in manifest
    assert "32.2" in manifest
