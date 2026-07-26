"""Tests — Enterprise AI Concierge (Sprint 29.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.concierge.catalogs import (
    GROUP_AI_CHAT_FOUNDATION,
    ORG_ACCESS,
    ROLES,
    WIZARD_STEPS,
)
from applications.platform_builder.shared.exceptions import ValidationError


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


def test_concierge_ready_and_catalog():
    health = platform_builder.health()
    assert health["application_version"] == "1.46.0"
    assert health["sprint"] == "32.3.4"
    assert health["concierge_builder_ready"] is True
    assert health["concierge_registry_ready"] is True
    assert health["organization_link_ready"] is True
    assert health["concierge_orchestration_ready"] is True
    assert health["concierge_preview_ready"] is True
    assert health["ai_team_center_ready"] is True
    assert health["group_ai_foundation_ready"] is True
    assert health["engines"]["concierge_builder"] == "1.0"
    assert health["engines"]["ai_team_center"] == "1.0"

    catalog = platform_builder.concierge.catalog()
    assert catalog["operational"] is True
    assert catalog["not_an_ai_agent"] is True
    assert catalog["ai_team_center_ready"] is True
    assert len(catalog["steps"]) == 11
    assert catalog["rules"]["one_per_organization"] is True
    assert catalog["rules"]["unlimited_ai_specialists"] is True
    assert any(r["id"] == "ceo_assistant" for r in ROLES)
    assert any(a["id"] == "ai_registry" for a in ORG_ACCESS)
    assert "purpose" in ORG_ACCESS[0]["help"]
    assert "Possible errors" not in ORG_ACCESS[0]["help"]["purpose"]
    assert len(WIZARD_STEPS) == 11
    assert GROUP_AI_CHAT_FOUNDATION["status"] == "operational"


def test_wizard_create_one_per_org_and_registry():
    session = platform_builder.concierge.start_session(organization_id="org_alpha")
    assert session["organization_id"] == "org_alpha"
    assert session["existing_concierge_id"] is None

    draft = {
        "name": "Nova",
        "avatar": "avatar_guide",
        "gender": "neutral",
        "voice_profile": "warm",
        "communication_style": "mentor",
        "role": "business_concierge",
        "organization_access": ["crm", "ai_registry", "analytics", "calendar"],
        "orchestration": ["delegate_tasks", "invite_specialists", "coordinate_team"],
        "proactive": ["morning_briefing", "daily_digest"],
        "owner_relationship": "business_partner",
        "recommendations": ["recommend_specialists", "recommend_workflows"],
    }
    platform_builder.concierge.update_session(session["session_id"], {"step": 10, "draft": draft})
    summary = platform_builder.concierge.summary(session["session_id"])
    assert summary["title"] == "Concierge Card"
    assert summary["card"]["identity"]["name"] == "Nova"
    assert "organization_overview" in summary
    assert "ai_team_overview" in summary
    assert summary["group_ai_chat"]["status"] == "operational"

    preview = platform_builder.concierge.conversation_preview(draft)
    assert preview["preview"][1]["role"] == "concierge"
    assert "Nova" in preview["preview"][1]["text"]

    created = platform_builder.concierge.create(session["session_id"])
    assert created["ok"] is True
    assert created["concierge"]["not_an_ai_agent"] is True
    assert created["concierge"]["linked_to_organization"] is True
    assert created["organization_link"]["organization_id"] == "org_alpha"
    assert created["registry"]["count"] == 1
    assert created["ai_team_center"]["organization_id"] == "org_alpha"
    assert created["ai_team_center"]["concierge_id"] == created["concierge"]["concierge_id"]
    assert created["group_ai_chat"]["status"] == "operational"

    # Exactly one Concierge per organization
    again = platform_builder.concierge.start_session(organization_id="org_alpha")
    again["draft"].update({"name": "Second", "role": "ceo_assistant"})
    platform_builder.concierge.update_session(again["session_id"], {"draft": again["draft"]})
    with pytest.raises(ValidationError):
        platform_builder.concierge.create(again["session_id"])

    # Different organization is allowed
    other = platform_builder.concierge.start_session(organization_id="org_beta")
    other["draft"].update({"name": "Atlas", "role": "executive_assistant"})
    platform_builder.concierge.update_session(other["session_id"], {"draft": other["draft"]})
    second = platform_builder.concierge.create(other["session_id"])
    assert second["ok"] is True
    assert platform_builder.concierge.registry.list_all()["count"] == 2


@pytest.mark.asyncio
async def test_api_concierge(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["concierge_builder_ready"] is True
    assert body["ai_team_center_ready"] is True
    assert body["application_version"] == "1.46.0"

    catalog = await client.get(f"{PREFIX}/concierge/catalog")
    assert catalog.status == 200
    cat = await catalog.json()
    assert cat["not_an_ai_agent"] is True
    assert len(cat["steps"]) == 11

    session = await client.post(
        f"{PREFIX}/concierge/sessions",
        json={"organization_id": "org_api"},
    )
    assert session.status == 201
    sid = (await session.json())["session_id"]

    patch = await client.patch(
        f"{PREFIX}/concierge/sessions/{sid}",
        json={
            "draft": {
                "name": "Echo",
                "avatar": "avatar_spark",
                "gender": "female",
                "voice_profile": "clear",
                "communication_style": "friendly",
                "role": "personal_concierge",
                "organization_access": ["crm", "tasks", "notifications"],
                "orchestration": ["prepare_meetings", "create_executive_reports"],
                "proactive": ["upcoming_meetings", "opportunity_detection"],
                "owner_relationship": "balanced",
                "recommendations": ["recommend_dashboards"],
            }
        },
    )
    assert patch.status == 200

    preview = await client.post(
        f"{PREFIX}/concierge/preview",
        json={"name": "Echo", "communication_style": "direct"},
    )
    assert preview.status == 200

    summary = await client.get(f"{PREFIX}/concierge/sessions/{sid}/summary")
    assert summary.status == 200
    summary_body = await summary.json()
    assert "ai_team_overview" in summary_body

    create = await client.post(f"{PREFIX}/concierge/sessions/{sid}/create", json={})
    assert create.status == 201
    created = await create.json()
    assert created["concierge"]["organization_id"] == "org_api"
    assert created["ai_team_center"]["organization_id"] == "org_api"

    registry = await client.get(f"{PREFIX}/concierge/registry")
    assert registry.status == 200
    assert (await registry.json())["count"] >= 1

    org = await client.get(f"{PREFIX}/concierge/organizations/org_api")
    assert org.status == 200
    assert (await org.json())["concierge"]["name"] == "Echo"

    # Duplicate create blocked
    dup = await client.post(f"{PREFIX}/concierge/sessions", json={"organization_id": "org_api"})
    dup_id = (await dup.json())["session_id"]
    await client.patch(
        f"{PREFIX}/concierge/sessions/{dup_id}",
        json={"draft": {"name": "Dup", "role": "ceo_assistant"}},
    )
    blocked = await client.post(f"{PREFIX}/concierge/sessions/{dup_id}/create", json={})
    assert blocked.status == 400


def test_docs_and_frontend_28_3():
    assert (ROOT / "docs" / "AI_CONCIERGE.md").exists()
    assert (ROOT / "docs" / "AI_TEAM_CENTER.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "concierge" / "README.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "ai_team" / "README.md").exists()
    assert (ROOT / "applications" / "platform_builder" / "concierge" / "wizard.py").exists()
    assert (ROOT / "applications" / "platform_builder" / "ai_team" / "team_center.py").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "concierge" / "ConciergeWizard.tsx").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "ai-team" / "AITeamCenterPage.tsx").exists()
    docs = (ROOT / "docs" / "AI_CONCIERGE.md").read_text()
    for key in ("one Concierge", "not", "AI Agent", "Orchestration", "Concierge Registry", "AI Team Center"):
        assert key in docs
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.46.0"' in manifest
    assert "32.3.4" in manifest
