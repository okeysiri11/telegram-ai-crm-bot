"""Tests — Live Organization (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.team_map.catalogs import (
    AI_CITY_APIS,
    EVENT_CHANNELS,
    RELATIONSHIP_TYPES,
    VISUAL_OBJECT_FIELDS,
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


def test_live_organization_engines():
    health = platform_builder.health()
    assert health["application_version"] == "1.40.0"
    assert health["sprint"] == "32.0"
    assert health["live_organization_ready"] is True
    assert health["relationship_engine_ready"] is True
    assert health["visual_event_bus_connected"] is True

    tm = platform_builder.team_map
    rel = tm.relationship_map()
    assert rel["count"] >= 1
    for r in RELATIONSHIP_TYPES:
        assert r in rel["by_category"]

    activity = tm.live_activity()
    assert "Current Conversations" in activity["channels"]

    sub = tm.bus_subscribe(["AI Events", "Task Events"])
    assert sub["active"] is True
    assert tm.event_bus.status()["connected"] is True
    polled = tm.bus_poll()
    assert polled["auto_refresh_ui"] is True
    assert polled["count"] >= 1
    assert set(EVENT_CHANNELS).issubset(set(polled["channels"]))

    visuals = tm.visual_objects()
    assert visuals["count"] >= 1
    for field in VISUAL_OBJECT_FIELDS:
        assert field in visuals["objects"][0]

    city = tm.ai_city_apis()
    for name in AI_CITY_APIS:
        assert name in city["apis"]
    assert city["apis"]["Movement API"]["planned"] is True
    assert city["animation_layer"]["operational"] is True


@pytest.mark.asyncio
async def test_api_live_organization(client):
    rel = await client.get(f"{PREFIX}/team-map/relationships")
    assert rel.status == 200

    activity = await client.get(f"{PREFIX}/team-map/activity")
    assert activity.status == 200

    sub = await client.post(
        f"{PREFIX}/team-map/events/subscribe",
        json={"channels": ["Organization Events"]},
    )
    assert sub.status == 201

    poll = await client.get(f"{PREFIX}/team-map/events/poll")
    assert poll.status == 200
    assert (await poll.json())["auto_refresh_ui"] is True

    objs = await client.get(f"{PREFIX}/team-map/visual-objects")
    assert objs.status == 200

    city = await client.get(f"{PREFIX}/team-map/ai-city-apis")
    assert city.status == 200

    filtered = await client.get(f"{PREFIX}/team-map/map?department=Finance&search=Finance")
    assert filtered.status == 200


def test_docs_live_organization_29_2():
    docs = (ROOT / "docs" / "LIVE_ORGANIZATION.md").read_text()
    for key in ("Visual Event Bus", "Relationship Engine", "Workload Engine", "Animation Layer"):
        assert key in docs
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"team_map": "1.0"' in manifest
    assert '"live_organization": "1.0"' in manifest
    assert '"visual_event_bus": "1.0"' in manifest
