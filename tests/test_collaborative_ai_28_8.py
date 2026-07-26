"""Tests — Collaborative AI Engine (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.collaborative_ai.catalogs import WIZARD_STEPS


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


def test_collaborative_ai_ready():
    health = platform_builder.health()
    assert health["application_version"] == "1.59.0"
    assert health["sprint"] == "33.3"
    assert health["collaborative_ai_ready"] is True
    assert health["collective_intelligence_ready"] is True
    assert health["decision_engine_ready"] is True
    assert health["knowledge_exchange_ready"] is True
    assert health["ai_ops_foundation_ready"] is True
    assert health["engines"]["collaborative_ai"] == "1.0"
    assert health["engines"]["collective_intelligence"] == "1.0"
    assert health["collaborative_ai"]["operational"] is True

    catalog = platform_builder.collaborative_ai.catalog()
    assert catalog["operational"] is True
    assert catalog["version"] == "1.0.0"
    assert len(catalog["steps"]) == 11
    assert len(WIZARD_STEPS) == 11
    assert catalog["group_ai_foundation"]["status"] == "operational"


def test_team_session_decision_create_flow():
    eng = platform_builder.collaborative_ai
    team = eng.create_team(
        {
            "team_name": "Clinic Collective",
            "business_goal": "Recommend staffing plan",
            "priority": "high",
        }
    )
    assert team["visual_id"]
    assert team["logical_state"]["visualization_ready"] is True

    roles = eng.assign_roles(team["team_id"])
    assert roles["count"] >= 2
    assert any(r["role"] == "Orchestrator" for r in roles["roles"])

    session = eng.start_collab_session(team["team_id"], topic="Staffing plan")
    workspace = eng.session_workspace(session["session_id"])
    assert workspace["participants"]
    assert workspace["consensus_status"] == "forming"

    tasks = eng.distribute_tasks(session["session_id"])
    assert tasks["balanced"] is True
    assert tasks["completed"] == tasks["assigned"]

    knowledge = eng.share_knowledge(session["session_id"])
    assert knowledge["entries"]
    assert knowledge["conclusions"]

    decision = eng.decide(session["session_id"])
    assert decision["recommended_decision"]
    assert decision["alternatives"]
    assert decision["business_impact"]

    report = eng.executive_summary(session["session_id"])
    assert report["executive_summary"]
    assert report["action_plan"]

    perf = eng.performance(session["session_id"])
    assert "Completed Tasks" in perf["metrics"]

    explain = eng.explain_decision(session["session_id"])
    for key in (
        "why_this_recommendation",
        "business_benefits",
        "alternative_approaches",
        "expected_result",
    ):
        assert key in explain

    ops = eng.ops_foundation(team_id=team["team_id"], session_id=session["session_id"])
    assert ops["ai_city_2d_integration_ready"] is True
    assert ops["objects"]

    wizard = eng.start_wizard()
    eng.update_wizard(
        wizard["session_id"],
        {
            "draft": {
                "team_name": "Ops Collective",
                "business_goal": "Unify specialist answers",
                "priority": "medium",
            }
        },
    )
    created = eng.create(wizard["session_id"])
    assert created["ok"] is True
    assert created["ai_team"]["team_id"]
    assert created["collaborative_session"]["session_id"]
    assert created["decision_engine"]["decision_id"]
    assert created["knowledge_exchange"]["exchange_pack_id"]


@pytest.mark.asyncio
async def test_api_collaborative_ai(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "1.59.0"
    assert body["collaborative_ai_ready"] is True

    catalog = await client.get(f"{PREFIX}/collaborative-ai/catalog")
    assert catalog.status == 200

    wizard = await client.post(
        f"{PREFIX}/collaborative-ai/wizard/sessions",
        json={"owner_id": "owner"},
    )
    assert wizard.status == 201
    sid = (await wizard.json())["session_id"]

    create = await client.post(
        f"{PREFIX}/collaborative-ai/wizard/sessions/{sid}/create",
        json={},
    )
    assert create.status == 201
    created = await create.json()
    assert created["ok"] is True


def test_docs_collaborative_ai_28_8():
    assert (ROOT / "docs" / "COLLABORATIVE_AI.md").exists()
    assert (ROOT / "docs" / "ENTERPRISE_COLLECTIVE_INTELLIGENCE.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "collaborative_ai" / "README.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "teamwork" / "README.md").exists()
    assert (
        ROOT / "src" / "web" / "platform-builder" / "collaborative-ai" / "CollaborativeAIStudio.tsx"
    ).exists()
    docs = (ROOT / "docs" / "COLLABORATIVE_AI.md").read_text()
    for key in ("Task Distribution", "Decision Engine", "Executive Summary", "AI Ops Foundation"):
        assert key in docs
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.59.0"' in manifest
    assert "33.3" in manifest
