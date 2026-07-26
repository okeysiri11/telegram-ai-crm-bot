"""Tests — Enterprise Vertical Builder (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.vertical.catalogs import INDUSTRIES, MODULES, WIZARD_STEPS


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


def test_vertical_ready_and_catalog():
    health = platform_builder.health()
    assert health["application_version"] == "1.62.0"
    assert health["sprint"] == "33.6"
    assert health["vertical_builder_ready"] is True
    assert health["vertical_registry_ready"] is True
    assert health["platform_registry_ready"] is True
    assert health["visual_layer_ready"] is True
    assert health["organization_preview_ready"] is True
    assert health["engines"]["vertical_builder"] == "1.0"

    catalog = platform_builder.vertical.catalog()
    assert catalog["operational"] is True
    assert catalog["platform_registry_ready"] is True
    assert catalog["visual_layer_ready"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert any(i["id"] == "medical" for i in INDUSTRIES)
    assert any(m["id"] == "knowledge_base" for m in MODULES)
    assert "purpose" in MODULES[0]["help"]
    assert "Possible errors" not in MODULES[0]["help"]["purpose"]
    vertical = next(b for b in platform_builder.engine.list_builders()["items"] if b["id"] == "vertical")
    assert vertical["status"] == "operational"
    assert vertical["frame_only"] is False


def test_wizard_create_registers_platform_and_visual():
    session = platform_builder.vertical.start_session(organization_id="org_clinic")
    draft = {
        "name": "Bright Dental",
        "description": "Modern clinic vertical",
        "industry": "medical",
        "business_size": "small",
        "logo": "logo_mark",
        "brand_color": "ocean",
        "modules": ["crm", "documents", "knowledge_base", "calendar", "workflows"],
        "ai_mode": "connect_existing",
        "concierge_mode": "attach_existing",
        "dashboard_widgets": ["kpi_overview", "ai_team_status", "organization_map"],
        "departments": ["Leadership", "Clinical", "Front Desk"],
        "menus": ["Home", "Patients", "AI Team"],
        "owner_name": "Dr. Owner",
    }
    platform_builder.vertical.update_session(session["session_id"], {"step": 9, "draft": draft})

    preview = platform_builder.vertical.organization_preview(session["session_id"])
    assert preview["title"] == "Organization Map"
    assert preview["visual_layer_ready"] is True
    assert "future_ai_city_position" in preview
    assert "AI Operations Center" in preview["compatible_with"]

    summary = platform_builder.vertical.summary(session["session_id"])
    assert summary["title"] == "Vertical Card"
    assert summary["card"]["name"] == "Bright Dental"
    assert "modules" in summary["card"]
    assert "ai_team" in summary["card"]
    assert "concierge" in summary["card"]

    created = platform_builder.vertical.create(session["session_id"])
    assert created["ok"] is True
    assert created["platform_registry_connected"] is True
    assert created["ai_team_connected"] is True
    assert created["concierge_connected"] is True
    assert created["visual_layer"]["ready"] is True
    assert "AI Operations Center" in created["visual_layer"]["prepared_for"]
    assert created["bundle"]["count"] >= 6

    obj = created["bundle"]["registered_objects"][0]
    assert "logical" in obj
    assert "visual" in obj
    assert obj["logical"]["ready_for_ai_ops"] is True
    assert obj["visual"]["ready_for_ai_city"] is True

    registry = platform_builder.vertical.registry.list_all()
    assert registry["count"] == 1
    assert registry["object_count"] >= 6


@pytest.mark.asyncio
async def test_api_vertical(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["vertical_builder_ready"] is True
    assert body["application_version"] == "1.62.0"

    catalog = await client.get(f"{PREFIX}/vertical/catalog")
    assert catalog.status == 200
    assert len((await catalog.json())["steps"]) == 10

    session = await client.post(
        f"{PREFIX}/vertical/sessions",
        json={"organization_id": "org_api_v"},
    )
    assert session.status == 201
    sid = (await session.json())["session_id"]

    patch = await client.patch(
        f"{PREFIX}/vertical/sessions/{sid}",
        json={
            "draft": {
                "name": "Harbor Logistics",
                "description": "Port + logistics vertical",
                "industry": "logistics",
                "modules": ["erp", "warehouse", "analytics", "api"],
                "ai_mode": "connect_existing",
                "concierge_mode": "create_new",
                "dashboard_widgets": ["kpi_overview", "alerts"],
                "departments": ["Ops", "Fleet"],
            }
        },
    )
    assert patch.status == 200

    preview = await client.get(f"{PREFIX}/vertical/sessions/{sid}/preview")
    assert preview.status == 200
    assert (await preview.json())["visual_layer_ready"] is True

    summary = await client.get(f"{PREFIX}/vertical/sessions/{sid}/summary")
    assert summary.status == 200

    create = await client.post(f"{PREFIX}/vertical/sessions/{sid}/create", json={})
    assert create.status == 201
    created = await create.json()
    assert created["ok"] is True
    assert created["visual_layer"]["ready"] is True

    registry = await client.get(f"{PREFIX}/vertical/registry")
    assert registry.status == 200
    assert (await registry.json())["count"] >= 1


def test_docs_and_frontend_28_4():
    assert (ROOT / "docs" / "VERTICAL_BUILDER.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "vertical_builder" / "README.md").exists()
    assert (ROOT / "applications" / "platform_builder" / "vertical" / "wizard.py").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "vertical" / "VerticalWizard.tsx").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "pages" / "VerticalBuilderPage.tsx").exists()
    docs = (ROOT / "docs" / "VERTICAL_BUILDER.md").read_text()
    for key in ("Logical Representation", "Visual Representation", "Platform Registry", "Organization Preview"):
        assert key in docs
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.62.0"' in manifest
    assert "33.6" in manifest
