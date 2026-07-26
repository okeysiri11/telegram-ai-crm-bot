"""Tests — Scenario Analysis Engine (Sprint 29.17)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.twin_intelligence.catalogs import (
    SCENARIO_TYPES,
    UI_SURFACES,
    WHAT_IF_ACTIONS,
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


def test_scenario_analysis_surfaces():
    eng = platform_builder.twin_intelligence
    scenarios = eng.scenario_analysis()
    assert set(scenarios["types"]) == set(SCENARIO_TYPES)
    assert scenarios["changes_platform_state"] is False

    what_if = eng.what_if_engine()
    assert set(what_if["actions"]) == set(WHAT_IF_ACTIONS)
    assert what_if["analytical_only"] is True

    ui = eng.ui_dashboard()
    assert set(ui["surfaces"]) == set(UI_SURFACES)
    assert ui["read_only_intelligence_layer"] is True


@pytest.mark.asyncio
async def test_api_scenario_analysis(client):
    scenarios = await client.post(
        f"{PREFIX}/twin-intelligence/scenarios",
        json={"action": "prepare", "type": "Infrastructure Scaling"},
    )
    assert scenarios.status == 201
    body = await scenarios.json()
    assert body["created"]["type"] == "Infrastructure Scaling"

    what_if = await client.post(
        f"{PREFIX}/twin-intelligence/what-if",
        json={"action": "Department Merge", "input": {"departments": ["a", "b"]}},
    )
    assert what_if.status == 201
    assert (await what_if.json())["changes_platform_state"] is False

    impact = await client.get(f"{PREFIX}/twin-intelligence/impact")
    assert impact.status == 200

    risk = await client.get(f"{PREFIX}/twin-intelligence/risk")
    assert risk.status == 200

    capacity = await client.get(f"{PREFIX}/twin-intelligence/capacity")
    assert capacity.status == 200

    comparison = await client.post(
        f"{PREFIX}/twin-intelligence/comparison",
        json={"mode": "Risk Delta"},
    )
    assert comparison.status == 201

    ui = await client.get(f"{PREFIX}/twin-intelligence/ui")
    assert ui.status == 200

    docs = ROOT / "docs" / "SCENARIO_ANALYSIS_ENGINE.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "scenario_analysis" / "README.md"
    assert knowledge.exists()
