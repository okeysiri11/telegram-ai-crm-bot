"""Tests — Enterprise Branding (Sprint 29.5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.themes.catalogs import BRANDING_FIELDS


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


def test_enterprise_branding():
    health = platform_builder.health()
    assert health["branding_engine_ready"] is True
    assert health["application_version"] == "1.38.0"

    branding = platform_builder.themes.branding("acme_org")
    assert branding["ready"] is True
    assert set(branding["fields"]) == set(BRANDING_FIELDS)
    for field in BRANDING_FIELDS:
        assert field in branding["profile"]

    profile = platform_builder.themes.upsert_brand_profile(
        {
            "organization_id": "acme_org",
            "Logo": {"url": "/brand/acme.svg", "alt": "Acme"},
            "Brand Colors": {"primary": "#0EA5E9", "accent": "#F97316"},
            "Typography": {"display": "Acme Display", "body": "Acme Sans"},
        }
    )
    assert profile["brand_profile_id"]
    assert profile["contains_business_logic"] is False
    assert profile["Logo"]["url"] == "/brand/acme.svg"

    again = platform_builder.themes.branding("acme_org")
    assert again["profile"]["Brand Colors"]["primary"] == "#0EA5E9"

    registry = platform_builder.themes.registry.list_themes()
    assert registry["count"] >= 3
    assert registry["operational"] is True


@pytest.mark.asyncio
async def test_api_branding(client):
    get = await client.get(f"{PREFIX}/themes/branding?organization_id=demo")
    assert get.status == 200
    body = await get.json()
    assert "Logo" in body["fields"]

    post = await client.post(
        f"{PREFIX}/themes/branding",
        json={"organization_id": "demo", "Icons": {"set": "custom"}},
    )
    assert post.status == 201
    assert (await post.json())["Icons"]["set"] == "custom"

    docs = ROOT / "docs" / "ENTERPRISE_THEMES.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "branding" / "README.md"
    assert knowledge.exists()
