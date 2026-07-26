"""Tests — Visual Layer (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.operations_center.catalogs import (
    AI_CITY_INTERFACES,
    VISUAL_OBJECT_FIELDS,
)
from applications.platform_builder.operations_center.engine import VisualLayer


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


def test_visual_layer_projection_contract():
    health = platform_builder.health()
    assert health["application_version"] == "1.53.0"
    assert health["sprint"] == "32.7"
    assert health["visual_layer_ready"] is True
    assert health["engines"]["visual_layer"] == "1.0"

    layer = VisualLayer(platform_builder.store)
    catalog = layer.catalog()
    assert catalog["operational"] is True
    assert catalog["executes_business_logic"] is False
    assert len(catalog["interfaces"]) == len(AI_CITY_INTERFACES) == 5

    projected = layer.project(
        {
            "logical_id": "ai_demo",
            "object_type": "ai_specialist",
            "name": "Analyst",
            "status": "analyzing",
            "relationships": {"team": "team_1"},
        }
    )
    for field in VISUAL_OBJECT_FIELDS:
        assert field in projected
    assert projected["visual_id"].startswith("viz_")
    assert projected["current_state"] == "Analyzing"
    assert projected["visual_state"]["position"]["planned"] is True
    assert projected["visual_state"]["movement"]["planned"] is True

    foundation = layer.foundation()
    assert foundation["visual_layer_ready"] is True
    assert foundation["future_live_organization_ready"] is True


def test_visual_ids_and_ai_city():
    ops = platform_builder.operations_center
    all_ids = ops.visual_ids()
    assert all_ids["count"] >= 1
    sample = all_ids["objects"][0]
    one = ops.visual_ids(sample["logical_id"])
    assert one["object"]["logical_id"] == sample["logical_id"]
    assert one["object"]["visual_id"] == sample["visual_id"]

    city = ops.ai_city_foundation()
    assert "Visual Layer" in city["interfaces"]
    assert city["positioning_schema"]["planned"] is True
    assert city["sample_objects"]


@pytest.mark.asyncio
async def test_api_visual_layer(client):
    layer = await client.get(f"{PREFIX}/operations/visual-layer")
    assert layer.status == 200
    body = await layer.json()
    assert body["ready"] is True

    ids = await client.get(f"{PREFIX}/operations/visual-ids")
    assert ids.status == 200

    live = await client.get(f"{PREFIX}/operations/live-status")
    assert live.status == 200

    wait = await client.get(f"{PREFIX}/operations/wait-experience")
    assert wait.status == 200
    wait_body = await wait.json()
    assert wait_body["empty_waiting"] is False

    city = await client.get(f"{PREFIX}/operations/ai-city")
    assert city.status == 200


def test_docs_visual_layer_29_1():
    docs = (ROOT / "docs" / "VISUAL_LAYER.md").read_text()
    for key in ("logical_id", "visual_id", "Future Positioning", "AI City"):
        assert key in docs
    assert (ROOT / "knowledge" / "visual_layer" / "README.md").exists()
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"visual_layer": "1.0"' in manifest
    assert '"live_status_engine": "1.0"' in manifest
