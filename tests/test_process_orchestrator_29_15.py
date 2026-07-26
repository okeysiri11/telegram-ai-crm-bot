"""Tests — Global Process Orchestrator (Sprint 30.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.workflow_intelligence.catalogs import (
    CRITICAL_PATH_FEATURES,
    ORCHESTRATION_TARGETS,
    RECOMMENDATION_TYPES,
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


def test_process_orchestrator_surfaces():
    health = platform_builder.health()
    assert health["global_process_orchestrator_ready"] is True
    assert health["application_version"] == "1.53.0"

    eng = platform_builder.workflow_intelligence
    critical = eng.critical_path()
    assert set(critical["features"]) == set(CRITICAL_PATH_FEATURES)

    recs = eng.workflow_recommendations()
    assert set(recs["types"]) == set(RECOMMENDATION_TYPES)

    orch = eng.enterprise_orchestration()
    assert set(orch["targets"]) == set(ORCHESTRATION_TARGETS)

    ui = eng.ui_dashboard()
    assert set(ui["surfaces"]) == set(UI_SURFACES)
    assert "Critical Path Viewer" in ui["surfaces"]
    assert ui["executes_business_logic"] is False


@pytest.mark.asyncio
async def test_api_process_orchestrator(client):
    deps = await client.get(f"{PREFIX}/workflow-intelligence/dependencies")
    assert deps.status == 200
    assert (await deps.json())["count"] >= 1

    critical = await client.get(f"{PREFIX}/workflow-intelligence/critical-path")
    assert critical.status == 200
    assert (await critical.json())["critical_workflow"]

    bottlenecks = await client.get(f"{PREFIX}/workflow-intelligence/bottlenecks")
    assert bottlenecks.status == 200

    orch = await client.post(
        f"{PREFIX}/workflow-intelligence/orchestration",
        json={"target": "Analytics"},
    )
    assert orch.status == 201
    assert (await orch.json())["last_target"] == "Analytics"

    ui = await client.get(f"{PREFIX}/workflow-intelligence/ui")
    assert ui.status == 200

    docs = ROOT / "docs" / "GLOBAL_PROCESS_ORCHESTRATOR.md"
    assert docs.exists()
    knowledge = ROOT / "knowledge" / "process_orchestration" / "README.md"
    assert knowledge.exists()
