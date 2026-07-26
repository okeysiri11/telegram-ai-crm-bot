"""Tests — Business Ecosystem Foundation (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.business_ecosystem.catalogs import (
    FRAMEWORK_COMPONENTS,
    UNIVERSAL_MODULES,
    WIZARD_STEPS,
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


def test_business_ecosystem_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.56.0"
    assert health["sprint"] == "33.0"
    assert health["business_ecosystem_foundation_ready"] is True
    assert health["universal_modules_ready"] is True
    assert health["industry_extension_system_ready"] is True
    assert health["automotive_ecosystem_prepared"] is True
    assert health["engines"]["business_ecosystem_framework"] == "1.0"
    assert health["engines"]["business_template_registry"] == "1.0"
    assert health["engines"]["reusable_module_registry"] == "1.0"
    assert health["engines"]["industry_extension_engine"] == "1.0"
    assert health["engines"]["industry_capability_registry"] == "1.0"
    assert health["business_ecosystem"]["does_not_replace_existing_modules"] is True
    assert health["business_ecosystem"]["does_not_break_existing_apis"] is True

    # Previous sprint surfaces remain compatible
    assert health["mission_control_ready"] is True
    assert health["digital_twin_ready"] is True
    assert health["strategy_engine_ready"] is True

    catalog = platform_builder.business_ecosystem.catalog()
    assert catalog["operational"] is True
    assert catalog["does_not_duplicate_existing_logic"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["components"]) == set(FRAMEWORK_COMPONENTS)
    assert len(catalog["universal_modules"]) == len(UNIVERSAL_MODULES)


def test_business_ecosystem_flow_and_create():
    eng = platform_builder.business_ecosystem
    framework = eng.framework_overview()
    assert "Industry Extension Engine" in framework["components"]
    assert "Mission Control" in framework["global_cores"]

    modules = eng.universal_modules(module="CRM")
    assert modules["selected"] == "CRM"
    assert modules["selected_module"]["extendable"] is True

    extensions = eng.extension_model()
    assert "custom AI agents" in extensions["extension_points"]
    assert extensions["nothing_is_copied"] is True

    registry = eng.ecosystem_registry(ecosystem="Automotive")
    assert registry["selected_ecosystem"]["prepared"] is True

    auto = eng.automotive_capabilities()
    assert "Vehicle Marketplace" in auto["capabilities"]
    assert auto["implements_from_scratch"] is False

    agri = eng.agriculture_capabilities()
    assert "Commodity Trading" in agri["capabilities"]

    beauty_cafe = eng.beauty_cafe_capabilities()
    assert beauty_cafe["beauty"]["ready"] is True
    assert beauty_cafe["cafe"]["ready"] is True

    cld = eng.crypto_legal_drone_capabilities()
    assert cld["crypto"]["ready"] is True
    assert cld["legal"]["ready"] is True
    assert cld["drone"]["ready"] is True

    compat = eng.architecture_compatibility(action="scan")
    assert compat["compatibility"]["existing_platform_works"] is True
    assert compat["compatibility"]["previous_sprints_compatible"] is True
    assert compat["prepared_for"] == "Automotive Business Ecosystem"

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["business_ecosystem_framework"]["business_ecosystem_framework_id"]
    assert created["business_template_registry"]["business_template_registry_id"]
    assert created["reusable_module_registry"]["reusable_module_registry_id"]
    assert created["industry_extension_engine"]["industry_extension_engine_id"]
    assert created["industry_capability_registry"]["industry_capability_registry_id"]


@pytest.mark.asyncio
async def test_api_business_ecosystem(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.56.0"
    assert body["business_ecosystem_foundation_ready"] is True
    assert body["mission_control_ready"] is True

    catalog = await client.get(f"{PREFIX}/business-ecosystem/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["does_not_break_existing_apis"] is True

    session = await client.post(f"{PREFIX}/business-ecosystem/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/business-ecosystem/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = (
        ROOT
        / "src"
        / "web"
        / "platform-builder"
        / "business-ecosystem"
        / "BusinessEcosystemStudio.tsx"
    )
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "BusinessEcosystemPage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "ENTERPRISE_BUSINESS_ECOSYSTEM.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "business_ecosystem" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.56.0"' in manifest
    assert "33.0" in manifest
