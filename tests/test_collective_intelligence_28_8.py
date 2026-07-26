"""Tests — Enterprise Collective Intelligence (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.collaborative_ai.catalogs import (
    EXPLAIN_FIELDS,
    OPS_FOUNDATION_SURFACES,
    PERFORMANCE_METRICS,
    ROLE_TEMPLATES,
)
from applications.platform_builder.shared.group_ai import GROUP_AI_CHAT_FOUNDATION


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


def test_collective_intelligence_surfaces():
    health = platform_builder.health()
    assert health["application_version"] == "1.34.0"
    assert health["sprint"] == "30.9"
    assert health["collective_intelligence_ready"] is True

    catalog = platform_builder.collaborative_ai.catalog()
    assert catalog["collective_intelligence_ready"] is True
    assert catalog["decision_engine_ready"] is True
    assert catalog["knowledge_exchange_ready"] is True
    assert len(catalog["role_templates"]) == len(ROLE_TEMPLATES)
    assert len(catalog["performance_metrics"]) == len(PERFORMANCE_METRICS) == 5
    assert len(catalog["explain_fields"]) == len(EXPLAIN_FIELDS) == 4
    assert len(catalog["ops_foundation_surfaces"]) == len(OPS_FOUNDATION_SURFACES) == 5

    assert GROUP_AI_CHAT_FOUNDATION["status"] == "operational"
    assert "collaborative_ai" in GROUP_AI_CHAT_FOUNDATION["runtime"]


def test_decision_engine_and_knowledge_exchange():
    eng = platform_builder.collaborative_ai
    team = eng.create_team({"team_name": "Risk Collective", "priority": "critical"})
    eng.assign_roles(team["team_id"])
    session = eng.start_collab_session(team["team_id"])
    eng.distribute_tasks(session["session_id"])
    exchange = eng.share_knowledge(
        session["session_id"],
        entries=[
            {
                "from": "Legal Specialist",
                "context": session["topic"],
                "reference": "policy:hr-12",
                "finding": "Compliance requires dual approval",
            }
        ],
    )
    assert exchange["entries"]
    decision = eng.decide(session["session_id"])
    assert len(decision["alternatives"]) >= 3
    assert decision["risk_notes"]
    assert decision["visual_id"]
    assert decision["logical_state"]["visualization_ready"] is True


@pytest.mark.asyncio
async def test_api_collective_intelligence_endpoints(client):
    team = await client.post(
        f"{PREFIX}/collaborative-ai/teams",
        json={"team_name": "API Collective", "business_goal": "Unify answers", "priority": "high"},
    )
    assert team.status == 201
    tid = (await team.json())["team_id"]

    roles = await client.post(f"{PREFIX}/collaborative-ai/teams/{tid}/roles", json={})
    assert roles.status == 200

    session = await client.post(
        f"{PREFIX}/collaborative-ai/teams/{tid}/sessions",
        json={"topic": "Unify answers"},
    )
    assert session.status == 201
    sid = (await session.json())["session_id"]

    workspace = await client.get(f"{PREFIX}/collaborative-ai/sessions/{sid}/workspace")
    assert workspace.status == 200

    tasks = await client.post(f"{PREFIX}/collaborative-ai/sessions/{sid}/tasks", json={})
    assert tasks.status == 200

    knowledge = await client.post(f"{PREFIX}/collaborative-ai/sessions/{sid}/knowledge", json={})
    assert knowledge.status == 200

    decide = await client.post(f"{PREFIX}/collaborative-ai/sessions/{sid}/decide", json={})
    assert decide.status == 200

    report = await client.get(f"{PREFIX}/collaborative-ai/sessions/{sid}/report")
    assert report.status == 200

    perf = await client.get(f"{PREFIX}/collaborative-ai/sessions/{sid}/performance")
    assert perf.status == 200

    explain = await client.get(f"{PREFIX}/collaborative-ai/sessions/{sid}/explain")
    assert explain.status == 200
    body = await explain.json()
    assert "why_this_recommendation" in body

    ops = await client.get(
        f"{PREFIX}/collaborative-ai/ops-foundation?team_id={tid}&session_id={sid}"
    )
    assert ops.status == 200
    ops_body = await ops.json()
    assert ops_body["visual_layer_ready"] is True


def test_docs_collective_intelligence_28_8():
    docs = (ROOT / "docs" / "ENTERPRISE_COLLECTIVE_INTELLIGENCE.md").read_text()
    for key in (
        "Decision Engine",
        "Knowledge Exchange",
        "AI Team Map",
        "2D AI City",
        "Contribution Cards",
    ):
        assert key in docs
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"collaborative_ai": "1.0"' in manifest
    assert '"collective_intelligence": "1.0"' in manifest
