"""Tests — Visual Theme Engine (Sprint 29.5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.themes.catalogs import THEME_SCOPES, WIZARD_STEPS


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


def test_theme_engine_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.21.0"
    assert health["sprint"] == "29.14"
    assert health["theme_engine_ready"] is True
    assert health["branding_engine_ready"] is True
    assert health["theme_registry_ready"] is True
    assert health["live_theme_switching_ready"] is True
    assert health["engines"]["theme_engine"] == "1.0"
    assert health["engines"]["theme_registry"] == "1.0"
    assert health["engines"]["branding_engine"] == "1.0"
    assert health["themes"]["contains_business_logic"] is False
    assert health["themes"]["affects_appearance_only"] is True

    catalog = platform_builder.themes.catalog()
    assert catalog["operational"] is True
    assert catalog["contains_business_logic"] is False
    assert catalog["affects_appearance_only"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["theme_scopes"]) == set(THEME_SCOPES)
    assert "dark" in catalog["modes"] and "light" in catalog["modes"]


def test_live_switch_and_create():
    eng = platform_builder.themes
    overview = eng.theme_engine_overview()
    assert overview["contains_business_logic"] is False
    assert len(overview["scopes"]) == 5

    colors = eng.color_system("dark")
    assert colors["palette"]["Primary"]
    assert "Status Colors" in colors["palette"]

    components = eng.component_theming("enterprise_dark")
    assert "Cards" in components["components"]
    assert "Buttons" in components["components"]

    a11y = eng.accessibility()
    assert a11y["reduced_motion"] is True
    assert a11y["color_safe_palette"] is True

    switched = eng.live_switch("enterprise_light")
    assert switched["ok"] is True
    assert switched["requires_restart"] is False
    assert switched["instant_visual_refresh"] is True
    assert switched["active_theme_id"] == "enterprise_light"
    assert eng.active_theme()["active_theme_id"] == "enterprise_light"

    city = eng.ai_city_foundation()
    assert "Building Themes" in city["interfaces"]

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10, "draft": {"mode": "light"}})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["theme_engine"]["theme_engine_id"]
    assert created["theme_registry"]["theme_registry_id"]
    assert created["brand_profile"]["brand_profile_id"]
    assert created["theme_engine"]["contains_business_logic"] is False


@pytest.mark.asyncio
async def test_api_themes(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.21.0"
    assert body["theme_engine_ready"] is True

    catalog = await client.get(f"{PREFIX}/themes/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["contains_business_logic"] is False

    switch = await client.post(f"{PREFIX}/themes/switch", json={"theme_id": "enterprise_light"})
    assert switch.status == 200
    assert (await switch.json())["instant_visual_refresh"] is True

    session = await client.post(f"{PREFIX}/themes/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/themes/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = ROOT / "src" / "web" / "platform-builder" / "themes" / "ThemeEngineStudio.tsx"
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "ThemeEnginePage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "VISUAL_THEME_ENGINE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "themes" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.21.0"' in manifest
    assert "29.14" in manifest
