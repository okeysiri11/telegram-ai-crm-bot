"""Tests — Resource Management (Sprint 29.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.assets.catalogs import OPTIMIZATION_FEATURES, VERSION_FEATURES


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


def test_version_and_optimization():
    health = platform_builder.health()
    assert health["version_management_ready"] is True
    assert health["optimization_engine_ready"] is True
    assert health["application_version"] == "1.19.0"

    eng = platform_builder.assets
    versions = eng.version_management("asset_org_logo")
    assert set(versions["features"]) == set(VERSION_FEATURES)
    assert versions["history"]["count"] >= 1

    replaced = eng.replace_asset(
        "asset_org_logo",
        {"uri": "/assets/org/logo_v2.svg", "compatible": True},
    )
    assert replaced["ok"] is True
    assert replaced["asset"]["version"] != "1.0.0"

    hist = eng.versions.history("asset_org_logo")
    assert hist["count"] >= 2

    rolled = eng.rollback_asset("asset_org_logo")
    assert rolled["ok"] is True

    opt = eng.resource_optimization()
    assert set(opt["feature_names"]) == set(OPTIMIZATION_FEATURES)
    assert opt["lazy_loading"] is True
    assert opt["caching"] is True
    assert opt["compression"] is True

    perf = eng.performance()
    assert "Memory Usage" in perf["metrics"]
    assert "Optimization Status" in perf["metrics"]


@pytest.mark.asyncio
async def test_api_resource_management(client):
    replace = await client.post(
        f"{PREFIX}/assets/replace",
        json={"asset_id": "asset_dept_icon", "uri": "/assets/dept/ops_v2.svg"},
    )
    assert replace.status == 200
    assert (await replace.json())["ok"] is True

    versions = await client.get(f"{PREFIX}/assets/versions?asset_id=asset_dept_icon")
    assert versions.status == 200
    assert (await versions.json())["ready"] is True

    rollback = await client.post(
        f"{PREFIX}/assets/rollback",
        json={"asset_id": "asset_dept_icon"},
    )
    assert rollback.status == 200
    assert (await rollback.json())["ok"] is True

    opt = await client.get(f"{PREFIX}/assets/optimization")
    assert opt.status == 200
    body = await opt.json()
    assert body["resource_pool_size"] >= 1

    docs = ROOT / "docs" / "RESOURCE_MANAGEMENT.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "resource_management" / "README.md"
    assert knowledge.exists()
