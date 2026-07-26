"""Tests — Visual Experience Engine (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.experience.catalogs import EXPERIENCE_COMPONENTS, WIZARD_STEPS


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


def test_visual_experience_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.32.0"
    assert health["sprint"] == "30.7"
    assert health["experience_engine_ready"] is True
    assert health["unified_ux_ready"] is True
    assert health["adaptive_interface_ready"] is True
    assert health["accessibility_operational"] is True
    assert health["engines"]["experience_engine"] == "1.0"
    assert health["engines"]["experience_registry"] == "1.0"
    assert health["engines"]["ux_rules_registry"] == "1.0"
    assert health["engines"]["adaptive_ui_registry"] == "1.0"
    assert health["experience"]["executes_business_logic"] is False

    catalog = platform_builder.experience.catalog()
    assert catalog["operational"] is True
    assert catalog["executes_business_logic"] is False
    assert catalog["presentation_coordination_only"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert set(catalog["components"]) == set(EXPERIENCE_COMPONENTS)


def test_experience_flow_and_create():
    eng = platform_builder.experience
    overview = eng.engine_overview()
    assert overview["executes_business_logic"] is False
    assert "Experience Engine" in overview["components"]

    unified = eng.unified_experience()
    assert unified["seamless"] is True
    assert "Visual Director Engine" in unified["subsystem_names"]

    ctx = eng.user_context("Executive Context")
    assert ctx["active_context"] == "Executive Context"

    adaptive = eng.adaptive_interface()
    assert "Screen Density" in adaptive["dimensions"]

    transitions = eng.transitions("Dashboard Transition", "ops")
    assert len(transitions["recent"]) >= 1

    rules = eng.global_rules()
    assert "Visual Consistency" in rules["rule_names"]

    cognitive = eng.cognitive_load_control()
    assert "Information Overload" in cognitive["controls"]

    workspaces = eng.multi_workspace(action="create", name="Secondary")
    assert len(workspaces["workspaces"]) >= 2

    a11y = eng.accessibility()
    assert a11y["accessibility_ready"] is True

    session = eng.start_session()
    eng.update_session(session["session_id"], {"step": 10, "draft": {"context": "Operator Context"}})
    created = eng.create(session["session_id"])
    assert created["ok"] is True
    assert created["experience_engine"]["experience_engine_id"]
    assert created["experience_registry"]["experience_registry_id"]
    assert created["ux_rules_registry"]["ux_rules_registry_id"]
    assert created["adaptive_ui_registry"]["adaptive_ui_registry_id"]
    assert created["experience_engine"]["executes_business_logic"] is False


@pytest.mark.asyncio
async def test_api_experience(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.32.0"
    assert body["experience_engine_ready"] is True

    catalog = await client.get(f"{PREFIX}/experience/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["executes_business_logic"] is False

    session = await client.post(f"{PREFIX}/experience/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/experience/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True

    studio = (
        ROOT / "src" / "web" / "platform-builder" / "experience" / "ExperienceEngineStudio.tsx"
    )
    page = ROOT / "src" / "web" / "platform-builder" / "pages" / "ExperienceEnginePage.tsx"
    assert studio.exists()
    assert page.exists()

    docs = ROOT / "docs" / "VISUAL_EXPERIENCE_ENGINE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "experience" / "README.md"
    assert knowledge.exists()

    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.32.0"' in manifest
    assert "30.7" in manifest
