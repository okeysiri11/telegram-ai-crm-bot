"""Tests — Business Ecosystem Capability Catalogs (Sprint 30.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.business_ecosystem.catalogs import (
    AGRICULTURE_CAPABILITIES,
    AUTOMOTIVE_CAPABILITIES,
    BEAUTY_CAPABILITIES,
    CAFE_CAPABILITIES,
    CRYPTO_CAPABILITIES,
    DRONE_CAPABILITIES,
    ECOSYSTEM_REGISTRY,
    LEGAL_CAPABILITIES,
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


def test_capability_catalogs():
    eng = platform_builder.business_ecosystem
    assert set(eng.automotive_capabilities()["capabilities"]) == set(AUTOMOTIVE_CAPABILITIES)
    assert set(eng.agriculture_capabilities()["capabilities"]) == set(AGRICULTURE_CAPABILITIES)
    beauty_cafe = eng.beauty_cafe_capabilities()
    assert set(beauty_cafe["beauty"]["capabilities"]) == set(BEAUTY_CAPABILITIES)
    assert set(beauty_cafe["cafe"]["capabilities"]) == set(CAFE_CAPABILITIES)
    cld = eng.crypto_legal_drone_capabilities()
    assert set(cld["crypto"]["capabilities"]) == set(CRYPTO_CAPABILITIES)
    assert set(cld["legal"]["capabilities"]) == set(LEGAL_CAPABILITIES)
    assert set(cld["drone"]["capabilities"]) == set(DRONE_CAPABILITIES)
    registry = eng.ecosystem_registry()
    assert set(registry["ecosystems"]) == set(ECOSYSTEM_REGISTRY)
    ui = eng.ui_dashboard()
    assert set(ui["surfaces"]) == set(UI_SURFACES)


@pytest.mark.asyncio
async def test_api_capability_catalogs(client):
    automotive = await client.get(f"{PREFIX}/business-ecosystem/automotive")
    assert automotive.status == 200
    assert (await automotive.json())["connects_universal_modules"] is True

    agriculture = await client.get(f"{PREFIX}/business-ecosystem/agriculture")
    assert agriculture.status == 200

    beauty_cafe = await client.get(f"{PREFIX}/business-ecosystem/beauty-cafe")
    assert beauty_cafe.status == 200

    cld = await client.get(f"{PREFIX}/business-ecosystem/crypto-legal-drone")
    assert cld.status == 200

    modules = await client.get(f"{PREFIX}/business-ecosystem/modules")
    assert modules.status == 200
    assert (await modules.json())["count"] >= 26

    compat = await client.post(
        f"{PREFIX}/business-ecosystem/compatibility",
        json={"action": "scan"},
    )
    assert compat.status == 201
    body = await compat.json()
    assert body["compatibility"]["no_duplicated_services"] is True

    docs = ROOT / "docs" / "BUSINESS_ECOSYSTEM_CAPABILITIES.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "industry_capabilities" / "README.md"
    assert knowledge.exists()
