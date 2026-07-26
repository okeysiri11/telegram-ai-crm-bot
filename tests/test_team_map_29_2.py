"""Tests — AI Team Map (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.team_map.catalogs import LIVE_STATUSES, WIZARD_STEPS


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


def test_team_map_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.25.0"
    assert health["sprint"] == "29.18"
    assert health["team_map_ready"] is True
    assert health["live_organization_ready"] is True
    assert health["relationship_engine_ready"] is True
    assert health["visual_event_bus_connected"] is True
    assert health["animation_layer_ready"] is True
    assert health["engines"]["team_map"] == "1.0"
    assert health["engines"]["live_organization"] == "1.0"
    assert health["engines"]["visual_event_bus"] == "1.0"

    catalog = platform_builder.team_map.catalog()
    assert catalog["operational"] is True
    assert catalog["ai_team_map_ready"] is True
    assert catalog["visual_event_bus_connected"] is True
    assert len(catalog["steps"]) == 10
    assert len(WIZARD_STEPS) == 10
    assert len(catalog["live_statuses"]) == len(LIVE_STATUSES) == 9
    assert "Reviewing" in catalog["live_statuses"]


def test_map_cards_workload_create():
    tm = platform_builder.team_map
    view = tm.map_view()
    assert view["nodes"]
    assert view["edges"]
    assert view["hierarchy"]["owner"]
    assert view["hierarchy"]["concierge"]
    assert view["hierarchy"]["specialists"]

    cards = tm.ai_cards()
    assert cards["count"] >= 1
    card = cards["cards"][0]
    for field in (
        "avatar",
        "name",
        "role",
        "specialization",
        "department",
        "current_status",
        "current_task",
        "current_workload",
        "knowledge_level",
        "health",
    ):
        assert field in card

    live = tm.live_status()
    for s in LIVE_STATUSES:
        assert s in live["counts"]

    workload = tm.workload_overview()
    assert "average_load" in workload
    assert "Balanced Work Indicator" in workload["metrics"] or any(
        "Balanced" in m for m in workload["metrics"]
    )

    session = tm.start_session()
    tm.update_session(session["session_id"], {"step": 10})
    created = tm.create(session["session_id"])
    assert created["ok"] is True
    assert created["organization_map"]["organization_map_id"]
    assert created["relationship_engine"]["relationship_engine_id"]
    assert created["workload_engine"]["workload_engine_id"]
    assert created["animation_layer"]["animation_layer_id"]
    assert created["event_bus"]["connected"] is True


@pytest.mark.asyncio
async def test_api_team_map(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.25.0"
    assert body["team_map_ready"] is True

    catalog = await client.get(f"{PREFIX}/team-map/catalog")
    assert catalog.status == 200

    m = await client.get(f"{PREFIX}/team-map/map")
    assert m.status == 200

    session = await client.post(f"{PREFIX}/team-map/sessions", json={})
    assert session.status == 201
    sid = (await session.json())["session_id"]

    create = await client.post(f"{PREFIX}/team-map/sessions/{sid}/create", json={})
    assert create.status == 201
    assert (await create.json())["ok"] is True


def test_docs_team_map_29_2():
    assert (ROOT / "docs" / "AI_TEAM_MAP.md").exists()
    assert (ROOT / "docs" / "LIVE_ORGANIZATION.md").exists()
    assert (ROOT / "knowledge" / "operations" / "team_map" / "README.md").exists()
    assert (ROOT / "knowledge" / "operations" / "live_organization" / "README.md").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "team-map" / "TeamMapStudio.tsx").exists()
    docs = (ROOT / "docs" / "AI_TEAM_MAP.md").read_text()
    for key in ("Visual Event Bus", "Workload Engine", "Relationship Map", "Zoom"):
        assert key in docs
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.25.0"' in manifest
    assert "29.18" in manifest
