"""Tests — AI Team Center (Sprint 28.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.concierge.catalogs import TEAM_OWNER_ACTIONS


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


def test_ai_team_center_dashboard_and_actions():
    status = platform_builder.ai_team.status()
    assert status["ready"] is True
    assert status["group_ai_chat_foundation"] is True
    assert set(status["owner_actions"]) == set(TEAM_OWNER_ACTIONS)

    dash = platform_builder.ai_team.dashboard("org_team")
    assert dash["ready"] is True
    assert dash["count"] >= 1
    member = dash["members"][0]
    for key in (
        "name",
        "avatar",
        "profession",
        "specialization",
        "status",
        "current_task",
        "memory_usage",
        "last_activity",
        "capabilities",
    ):
        assert key in member

    agent_id = member["agent_id"]
    paused = platform_builder.ai_team.action("org_team", agent_id, "pause_agent")
    assert paused["ok"] is True
    assert paused["member"]["status"] == "paused"

    resumed = platform_builder.ai_team.action("org_team", agent_id, "resume_agent")
    assert resumed["member"]["status"] == "active"

    assigned = platform_builder.ai_team.action(
        "org_team", agent_id, "assign_task", {"task": "Prepare board pack"}
    )
    assert assigned["member"]["current_task"] == "Prepare board pack"

    foundation = platform_builder.ai_team.group_chat_foundation()
    assert foundation["status"] == "operational"
    assert "Lawyer" in foundation["invite_roles"]
    assert "conversation_history" in foundation["model"]
    assert "decision_summary" in foundation["model"]


def test_concierge_registers_ai_team_center():
    session = platform_builder.concierge.start_session(organization_id="org_link")
    platform_builder.concierge.update_session(
        session["session_id"],
        {"draft": {"name": "Iris", "role": "ceo_assistant"}},
    )
    created = platform_builder.concierge.create(session["session_id"])
    center = created["ai_team_center"]
    assert center["concierge_id"] == created["concierge"]["concierge_id"]
    loaded = platform_builder.ai_team.get_center("org_link")
    assert loaded is not None
    assert loaded["team_center_id"] == center["team_center_id"]


@pytest.mark.asyncio
async def test_api_ai_team(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["ai_team_center_ready"] is True
    assert body["ai_dashboard_ready"] is True
    assert body["group_ai_foundation_ready"] is True

    dash = await client.get(f"{PREFIX}/ai-team/organizations/org_api_team/dashboard")
    assert dash.status == 200
    data = await dash.json()
    assert data["count"] >= 1
    agent_id = data["members"][0]["agent_id"]

    action = await client.post(
        f"{PREFIX}/ai-team/organizations/org_api_team/actions",
        json={"agent_id": agent_id, "action": "view_knowledge", "payload": {}},
    )
    assert action.status == 200
    assert (await action.json())["ok"] is True

    group = await client.get(f"{PREFIX}/ai-team/group-chat")
    assert group.status == 200
    assert (await group.json())["status"] == "operational"

    st = await client.get(f"{PREFIX}/ai-team/status")
    assert st.status == 200


def test_docs_ai_team_28_3():
    assert (ROOT / "docs" / "AI_TEAM_CENTER.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "ai_team" / "README.md").exists()
    docs = (ROOT / "docs" / "AI_TEAM_CENTER.md").read_text()
    for key in ("AI Team Center", "Unlimited", "Group AI Chat", "Pause Agent"):
        assert key in docs
