"""Tests — Enterprise AI Operations Center (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.operations_center.catalogs import (
    DASHBOARD_CATEGORIES,
    LIVE_STATUSES,
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


def test_operations_center_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.47.0"
    assert health["sprint"] == "32.3.5"
    assert health["operations_center_ready"] is True
    assert health["live_status_engine_ready"] is True
    assert health["visual_layer_ready"] is True
    assert health["status_dashboard_ready"] is True
    assert health["engines"]["operations_center"] == "1.0"
    assert health["engines"]["visual_layer"] == "1.0"
    assert health["engines"]["live_status_engine"] == "1.0"
    assert health["operations_center"]["operational"] is True
    assert health["operations_center"]["executes_business_logic"] is False

    catalog = platform_builder.operations_center.catalog()
    assert catalog["operational"] is True
    assert catalog["executes_business_logic"] is False
    assert catalog["visualizes_logical_layer"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert len(catalog["dashboard_categories"]) == len(DASHBOARD_CATEGORIES) == 10
    assert len(catalog["live_statuses"]) == len(LIVE_STATUSES) == 9


def test_dashboard_live_wait_create_flow():
    ops = platform_builder.operations_center
    dash = ops.dashboard()
    assert dash["ready"] is True
    assert "Organizations" in dash["categories"]
    assert "Live Sessions" in dash["categories"]

    live = ops.live_status()
    assert live["total"] >= 1
    for status in LIVE_STATUSES:
        assert status in live["counts"]

    activity = ops.realtime_activity()
    assert activity["active_count"] >= 0
    assert "Current Tasks" in activity["channels"]

    wait = ops.wait_experience()
    assert wait["empty_waiting"] is False
    assert wait["misrepresents_state"] is False
    assert "Active Specialists" in wait["stages"]

    teams = ops.team_overview()
    assert "availability" in teams
    assert teams["performance"]

    health = ops.system_health()
    assert "Platform Health" in health["surfaces"]

    summary = ops.ops_summary()
    assert "organization_status" in summary
    assert "ai_status" in summary
    assert "health" in summary

    session = ops.start_session()
    ops.update_session(session["session_id"], {"step": 10})
    created = ops.create(session["session_id"])
    assert created["ok"] is True
    assert created["operations_center"]["operations_center_id"]
    assert created["visual_layer"]["visual_layer_id"]
    assert created["status_engine"]["status_engine_id"]
    assert created["operations_center"]["executes_business_logic"] is False


@pytest.mark.asyncio
async def test_api_operations_center(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.47.0"
    assert body["operations_center_ready"] is True

    catalog = await client.get(f"{PREFIX}/operations/catalog")
    assert catalog.status == 200

    dash = await client.get(f"{PREFIX}/operations/dashboard")
    assert dash.status == 200

    session = await client.post(f"{PREFIX}/operations/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/operations/sessions/{sid}/create", json={})
    assert create.status == 201
    created = await create.json()
    assert created["ok"] is True


def test_docs_operations_center_29_1():
    assert (ROOT / "docs" / "AI_OPERATIONS_CENTER.md").exists()
    assert (ROOT / "docs" / "VISUAL_LAYER.md").exists()
    assert (ROOT / "knowledge" / "operations" / "README.md").exists()
    assert (ROOT / "knowledge" / "visual_layer" / "README.md").exists()
    assert (
        ROOT / "src" / "web" / "platform-builder" / "operations" / "OperationsCenterStudio.tsx"
    ).exists()
    docs = (ROOT / "docs" / "AI_OPERATIONS_CENTER.md").read_text()
    for key in ("Live Status Engine", "Wait Experience Engine", "Does not execute business logic"):
        assert key in docs
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.47.0"' in manifest
    assert "32.3.5" in manifest
