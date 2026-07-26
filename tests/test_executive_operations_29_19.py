"""Tests — Executive Operations Center (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.mission_control.catalogs import (
    HEALTH_DIMENSIONS,
    MISSION_PANELS,
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


def test_executive_operations_surfaces():
    eng = platform_builder.mission_control
    overview = eng.executive_overview()
    assert set(overview["dimensions"]) == set(HEALTH_DIMENSIONS)
    assert overview["read_only"] is True

    panels = eng.mission_panels()
    assert set(panels["panels"]) == set(MISSION_PANELS)
    assert panels["owns_business_logic"] is False

    ui = eng.ui_dashboard()
    assert set(ui["surfaces"]) == set(UI_SURFACES)
    assert ui["read_only_aggregation_layer"] is True
    assert "Executive Cockpit" in ui["surfaces"]


@pytest.mark.asyncio
async def test_api_executive_operations(client):
    overview = await client.get(f"{PREFIX}/mission-control/overview")
    assert overview.status == 200

    activity = await client.get(f"{PREFIX}/mission-control/activity")
    assert activity.status == 200

    panels = await client.post(
        f"{PREFIX}/mission-control/panels",
        json={"panel": "Critical Alerts"},
    )
    assert panels.status == 201
    assert (await panels.json())["selected"] == "Critical Alerts"

    decisions = await client.get(f"{PREFIX}/mission-control/decisions")
    assert decisions.status == 200

    resources = await client.get(f"{PREFIX}/mission-control/resources")
    assert resources.status == 200

    timeline = await client.get(f"{PREFIX}/mission-control/timeline")
    assert timeline.status == 200

    ui = await client.get(f"{PREFIX}/mission-control/ui")
    assert ui.status == 200
    assert "Executive Cockpit" in (await ui.json())["surfaces"]

    docs = ROOT / "docs" / "EXECUTIVE_OPERATIONS_CENTER.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "executive_operations" / "README.md"
    assert knowledge.exists()
