"""Tests — Visual Asset Registry (Sprint 29.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.assets.catalogs import ASSET_CATEGORIES, ASSET_TYPES, WIZARD_STEPS


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


def test_asset_registry_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.13.0"
    assert health["sprint"] == "29.6"
    assert health["visual_asset_registry_ready"] is True
    assert health["version_management_ready"] is True
    assert health["optimization_engine_ready"] is True
    assert health["asset_browser_ready"] is True
    assert health["engines"]["visual_asset_registry"] == "1.0"
    assert health["engines"]["version_registry"] == "1.0"
    assert health["engines"]["optimization_engine"] == "1.0"
    assert health["assets"]["contains_business_logic"] is False
    assert health["assets"]["separated_from_business_logic"] is True

    catalog = platform_builder.assets.catalog()
    assert catalog["operational"] is True
    assert catalog["contains_business_logic"] is False
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["asset_types"]) == set(ASSET_TYPES)
    assert set(catalog["categories"]) == set(ASSET_CATEGORIES)


def test_browser_search_create():
    eng = platform_builder.assets
    overview = eng.registry_overview()
    assert overview["count"] >= 5
    assert overview["separated_from_business_logic"] is True

    cats = eng.categories()
    assert "AI" in cats["counts"]

    browser = eng.browser()
    assert browser["preview_panel"] is True
    assert browser["category_explorer"] is True

    search = eng.search({"category": "AI"})
    assert search["count"] >= 1
    assert "Category" in search["facets"]

    avatars = eng.avatar_library()
    assert "Base Characters" in avatars["sections"]

    city = eng.ai_city_foundation()
    assert "Buildings" in city["interfaces"]

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["asset_registry"]["asset_registry_id"]
    assert created["version_registry"]["version_registry_id"]
    assert created["optimization_engine"]["optimization_engine_id"]
    assert created["asset_registry"]["contains_business_logic"] is False


@pytest.mark.asyncio
async def test_api_assets(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.13.0"
    assert body["visual_asset_registry_ready"] is True

    catalog = await client.get(f"{PREFIX}/assets/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["contains_business_logic"] is False

    browser = await client.get(f"{PREFIX}/assets/browser")
    assert browser.status == 200
    assert (await browser.json())["ready"] is True

    session = await client.post(f"{PREFIX}/assets/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/assets/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = ROOT / "src" / "web" / "platform-builder" / "assets" / "AssetRegistryStudio.tsx"
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "AssetRegistryPage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "VISUAL_ASSET_REGISTRY.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "assets" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.13.0"' in manifest
    assert "29.6" in manifest
