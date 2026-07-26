"""Tests — Universal Builder Framework (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.framework.catalogs import LIFECYCLE, WIZARD_STEPS


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


def test_ubf_ready_catalog_and_lifecycle():
    health = platform_builder.health()
    assert health["application_version"] == "1.30.0"
    assert health["sprint"] == "30.5"
    assert health["universal_builder_framework_ready"] is True
    assert health["builder_registry_ready"] is True
    assert health["template_engine_ready"] is True
    assert health["builder_sdk_foundation_ready"] is True
    assert health["engines"]["universal_builder_framework"] == "1.0"

    catalog = platform_builder.ubf.catalog()
    assert catalog["operational"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert list(LIFECYCLE) == catalog["lifecycle"]
    assert "Wizard" in catalog["ui_components"]
    assert any(r["id"] == "suggestion_engine" for r in catalog["validation_rules"])

    boot = platform_builder.ubf.bootstrap()
    assert boot["ok"] is True
    assert boot["seeded"]["count"] >= 10
    assert platform_builder.ubf.registry.list_all()["count"] >= 10


def test_validate_preview_create_template():
    session = platform_builder.ubf.start_session()
    platform_builder.ubf.update_session(
        session["session_id"],
        {
            "step": 9,
            "draft": {
                "name": "Document Studio",
                "builder_type": "document",
                "version": "1.0.0",
                "components": ["Wizard", "Forms", "Preview Window"],
                "validation_rules": ["required_fields", "duplicate_detection"],
                "save_as_template": True,
                "extensions": ["Plugins"],
                "dependencies": ["builder_engine"],
                "knowledge_topics": ["docs"],
            },
        },
    )

    validation = platform_builder.ubf.validate_session(session["session_id"])
    assert validation["ok"] is True
    assert "suggestion_engine" in validation["rules_checked"]

    preview = platform_builder.ubf.preview(session["session_id"])
    assert preview["instant_preview"] is True
    assert preview["visual_summary"]["title"] == "Document Studio"

    created = platform_builder.ubf.create(session["session_id"])
    assert created["ok"] is True
    assert created["builder"]["builder_type"] == "document"
    assert created["template"]["builder_type"] == "document"
    assert created["components"]["components"]
    assert created["schema"]["schema"]
    assert created["registry"]["count"] >= 1

    cloned = platform_builder.ubf.templates.clone(created["template"]["template_id"])
    assert cloned["name"].endswith("Copy")
    assert platform_builder.ubf.templates.list_all()["count"] >= 2


@pytest.mark.asyncio
async def test_api_ubf(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["universal_builder_framework_ready"] is True
    assert body["application_version"] == "1.30.0"

    boot = await client.post(f"{PREFIX}/ubf/bootstrap", json={})
    assert boot.status == 201

    catalog = await client.get(f"{PREFIX}/ubf/catalog")
    assert catalog.status == 200
    assert len((await catalog.json())["lifecycle"]) == 8

    session = await client.post(f"{PREFIX}/ubf/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    patch = await client.patch(
        f"{PREFIX}/ubf/sessions/{sid}",
        json={
            "draft": {
                "name": "Department Studio",
                "builder_type": "department",
                "components": ["Wizard", "Cards"],
                "validation_rules": ["required_fields"],
                "save_as_template": True,
            }
        },
    )
    assert patch.status == 200

    validate = await client.post(f"{PREFIX}/ubf/sessions/{sid}/validate", json={})
    assert validate.status == 200
    assert (await validate.json())["ok"] is True

    preview = await client.get(f"{PREFIX}/ubf/sessions/{sid}/preview")
    assert preview.status == 200

    summary = await client.get(f"{PREFIX}/ubf/sessions/{sid}/summary")
    assert summary.status == 200

    create = await client.post(f"{PREFIX}/ubf/sessions/{sid}/create", json={})
    assert create.status == 201
    created = await create.json()
    assert created["builder"]["builder_type"] == "department"

    registry = await client.get(f"{PREFIX}/ubf/registry")
    assert registry.status == 200
    assert (await registry.json())["count"] >= 1


def test_docs_and_frontend_28_5():
    assert (ROOT / "docs" / "UNIVERSAL_BUILDER_FRAMEWORK.md").exists()
    assert (ROOT / "docs" / "BUILDER_SDK.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "framework" / "README.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "sdk" / "README.md").exists()
    assert (ROOT / "applications" / "platform_builder" / "framework" / "engine.py").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "ubf" / "UniversalFrameworkStudio.tsx").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "framework" / "ConfirmationScreen.tsx").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "framework" / "LiveValidation.tsx").exists()
    docs = (ROOT / "docs" / "UNIVERSAL_BUILDER_FRAMEWORK.md").read_text()
    for key in ("Lifecycle", "Builder Registry", "Template Engine", "Validation"):
        assert key in docs
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.30.0"' in manifest
    assert "30.5" in manifest
