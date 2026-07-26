"""Tests — Enterprise Mission Control (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.mission_control.catalogs import (
    MISSION_COMPONENTS,
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


def test_mission_control_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.38.0"
    assert health["sprint"] == "31.3"
    assert health["mission_control_ready"] is True
    assert health["executive_operations_ready"] is True
    assert health["mission_dashboard_ready"] is True
    assert health["executive_cockpit_ready"] is True
    assert health["engines"]["mission_control"] == "1.0"
    assert health["engines"]["executive_operations_center"] == "1.0"
    assert health["engines"]["mission_registry"] == "1.0"
    assert health["engines"]["executive_api"] == "1.0"
    assert health["engines"]["mission_dashboard"] == "1.0"
    assert health["mission_control"]["executes_business_logic"] is False
    assert health["mission_control"]["owns_business_logic"] is False
    assert health["mission_control"]["replaces_existing_modules"] is False

    catalog = platform_builder.mission_control.catalog()
    assert catalog["operational"] is True
    assert catalog["read_only_aggregation_layer"] is True
    assert catalog["aggregates_existing_platform_services"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["components"]) == set(MISSION_COMPONENTS)


def test_mission_control_flow_and_create():
    eng = platform_builder.mission_control
    overview = eng.engine_overview()
    assert "Mission Coordinator" in overview["components"]

    operations = eng.unified_operations(action="aggregate")
    assert operations["last_refresh"]
    assert operations["replaces_existing_modules"] is False

    executive = eng.executive_overview(dimension="Platform Health")
    assert executive["selected"] == "Platform Health"

    activity = eng.global_activity(stream="AI Activity")
    assert activity["selected"] == "AI Activity"

    panels = eng.mission_panels(panel="Risk Center")
    assert panels["selected"] == "Risk Center"

    decisions = eng.decision_center(feature="Impact Comparison")
    assert decisions["selected"] == "Impact Comparison"

    resources = eng.resource_command(view="AI Teams")
    assert resources["selected"] == "AI Teams"

    timeline = eng.mission_timeline(segment="Milestones")
    assert timeline["selected"] == "Milestones"

    perf = eng.performance(action="realtime_aggregation")
    assert perf["cache"]["entries"] >= 1

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["mission_control"]["mission_control_id"]
    assert created["executive_operations_center"]["executive_operations_center_id"]
    assert created["mission_registry"]["mission_registry_id"]
    assert created["executive_api"]["executive_api_id"]
    assert created["mission_dashboard"]["mission_dashboard_id"]


@pytest.mark.asyncio
async def test_api_mission_control(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.38.0"
    assert body["mission_control_ready"] is True

    catalog = await client.get(f"{PREFIX}/mission-control/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["replaces_existing_modules"] is False

    session = await client.post(f"{PREFIX}/mission-control/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/mission-control/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = (
        ROOT / "src" / "web" / "platform-builder" / "mission-control" / "MissionControlStudio.tsx"
    )
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "MissionControlPage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "ENTERPRISE_MISSION_CONTROL.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "mission_control" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.38.0"' in manifest
    assert "31.3" in manifest
