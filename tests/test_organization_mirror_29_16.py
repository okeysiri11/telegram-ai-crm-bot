"""Tests — Organization Mirror (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.digital_twin.catalogs import (
    ORGANIZATION_MIRROR_ENTITIES,
    SNAPSHOT_TYPES,
    UI_SURFACES,
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


def test_organization_mirror_surfaces():
    health = platform_builder.health()
    assert health["organization_mirror_ready"] is True
    assert health["application_version"] == "1.59.0"

    eng = platform_builder.digital_twin
    org = eng.organization_mirror()
    assert set(org["entities"]) == set(ORGANIZATION_MIRROR_ENTITIES)
    assert org["read_only"] is True

    snapshots = eng.snapshot_engine()
    assert set(snapshots["types"]) == set(SNAPSHOT_TYPES)

    ui = eng.ui_dashboard()
    assert set(ui["surfaces"]) == set(UI_SURFACES)
    assert "Organization Mirror" in ui["surfaces"]
    assert ui["read_only_reflection_layer"] is True


@pytest.mark.asyncio
async def test_api_organization_mirror(client):
    org = await client.get(f"{PREFIX}/digital-twin/organization")
    assert org.status == 200
    body = await org.json()
    assert "Departments" in body["entities"]
    assert body["executes_business_logic"] is False

    sync = await client.post(f"{PREFIX}/digital-twin/sync", json={"mode": "incremental"})
    assert sync.status == 201
    assert (await sync.json())["ok"] is True

    snap = await client.post(
        f"{PREFIX}/digital-twin/snapshots",
        json={"action": "capture", "type": "Historical Snapshot", "label": "org-v1"},
    )
    assert snap.status == 201
    assert (await snap.json())["created"]["type"] == "Historical Snapshot"

    comparison = await client.post(
        f"{PREFIX}/digital-twin/comparison",
        json={"dimension": "Organization Versions"},
    )
    assert comparison.status == 201

    ui = await client.get(f"{PREFIX}/digital-twin/ui")
    assert ui.status == 200

    docs = ROOT / "docs" / "ORGANIZATION_MIRROR.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "organization_mirror" / "README.md"
    assert knowledge.exists()
