"""Tests — Enterprise AI Builder (Sprint 28.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.platform_builder.api.register import register_platform_builder_routes
from applications.platform_builder.ai_builder.catalogs import (
    AGENT_COUNTS,
    KNOWLEDGE_SOURCES,
    PROFESSIONS,
    SKILLS,
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


def test_ai_builder_ready_and_catalog():
    health = platform_builder.health()
    assert health["application_version"] == "1.16.0"
    assert health["sprint"] == "29.9"
    assert health["ai_builder_ready"] is True
    assert health["ai_wizard_ready"] is True
    assert health["multi_agent_builder_ready"] is True
    assert health["knowledge_selector_ready"] is True
    assert health["personality_builder_ready"] is True
    assert health["ai_registry_ready"] is True
    assert health["group_ai_chat_foundation_ready"] is True
    assert health["engines"]["ai_builder"] == "1.0"

    catalog = platform_builder.ai_builder.catalog()
    assert catalog["operational"] is True
    assert len(catalog["steps"]) == 10
    assert catalog["steps"][8]["title"] == "Summary"
    assert catalog["why_multi_agent"]["illustration"]["kind"] == "ai_team"
    assert len(AGENT_COUNTS) == 7
    assert any(p["id"] == "medical" for p in PROFESSIONS)
    assert any(k["id"] == "crm" for k in KNOWLEDGE_SOURCES)
    assert any(s["id"] == "answer_questions" for s in SKILLS)
    assert "purpose" in KNOWLEDGE_SOURCES[0]["help"]
    assert "Possible errors" not in KNOWLEDGE_SOURCES[0]["help"]["purpose"]
    assert catalog["group_ai_chat"]["status"] == "foundation"
    assert len(WIZARD_STEPS) == 10


def test_wizard_multi_agent_create_and_registry():
    session = platform_builder.ai_builder.start_session(agent_count=2)
    assert session["agent_count"] == 2
    assert session["multi_agent"] is True
    assert len(session["agents"]) == 2

    agents = session["agents"]
    agents[0].update(
        {
            "name": "Ava",
            "profession": "medical",
            "specialization": ["dentistry", "implantology"],
            "knowledge": ["crm", "documents", "knowledge_base"],
            "skills": ["answer_questions", "analyze_documents"],
            "permissions": ["read_crm", "read_knowledge"],
            "personality": {
                "gender": "female",
                "communication_style": "mentor",
                "professional_tone": "balanced",
                "conversation_style": "ask_clarify",
            },
        }
    )
    agents[1].update(
        {
            "name": "Noah",
            "profession": "finance",
            "specialization": ["treasury"],
            "knowledge": ["erp", "excel"],
            "skills": ["create_reports", "analytics"],
            "permissions": ["read_crm", "access_documents"],
            "personality": {
                "gender": "male",
                "communication_style": "business_professional",
                "professional_tone": "formal",
                "conversation_style": "lead_with_action",
            },
        }
    )
    updated = platform_builder.ai_builder.update_session(
        session["session_id"],
        {"step": 9, "agents": agents},
    )
    assert updated["step"] == 9

    summary = platform_builder.ai_builder.summary(session["session_id"])
    assert summary["title"] == "AI Team Summary"
    assert len(summary["cards"]) == 2
    assert summary["cards"][0]["name"] == "Ava"

    preview = platform_builder.ai_builder.personality_preview(
        {"communication_style": "friendly"},
        name="Ava",
    )
    assert preview["preview"][1]["role"] == "assistant"
    assert "Ava" in preview["preview"][1]["text"]

    tree = platform_builder.ai_builder.specializations("medical")
    assert tree["multi_select"] is True
    assert tree["tree"][0]["name"] == "Dentistry"

    created = platform_builder.ai_builder.create(session["session_id"])
    assert created["ok"] is True
    assert created["created_count"] == 2
    assert created["registry"]["count"] >= 2
    assert created["group_ai_chat"]["foundation"] is True
    assert all(a["lifecycle"] == "registered" for a in created["agents"])
    assert all(a["configuration_saved"] is True for a in created["agents"])

    with pytest.raises(ValidationError):
        platform_builder.ai_builder.start_session(agent_count=7)

    custom = platform_builder.ai_builder.start_session(agent_count="custom", custom_count=3)
    assert custom["agent_count"] == 3


@pytest.mark.asyncio
async def test_api_ai_builder(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["ai_builder_ready"] is True
    assert body["application_version"] == "1.16.0"

    catalog = await client.get(f"{PREFIX}/ai-builder/catalog")
    assert catalog.status == 200
    assert (await catalog.json())["operational"] is True

    session = await client.post(
        f"{PREFIX}/ai-builder/sessions",
        json={"agent_count": 1},
    )
    assert session.status == 201
    sid = (await session.json())["session_id"]

    patch = await client.patch(
        f"{PREFIX}/ai-builder/sessions/{sid}",
        json={
            "agents": [
                {
                    "slot": 1,
                    "name": "River",
                    "profession": "sales",
                    "specialization": ["outbound"],
                    "knowledge": ["crm"],
                    "skills": ["crm_operations"],
                    "permissions": ["read_crm", "create_records"],
                    "personality": {
                        "gender": "neutral",
                        "communication_style": "friendly",
                        "professional_tone": "casual",
                        "conversation_style": "offer_options",
                    },
                }
            ]
        },
    )
    assert patch.status == 200

    names = await client.get(f"{PREFIX}/ai-builder/names?gender=female")
    assert names.status == 200
    assert "Ava" in (await names.json())["suggestions"]

    specs = await client.get(f"{PREFIX}/ai-builder/specializations/medical")
    assert specs.status == 200

    personality = await client.post(
        f"{PREFIX}/ai-builder/personality-preview",
        json={"name": "River", "personality": {"communication_style": "direct"}},
    )
    assert personality.status == 200

    summary = await client.get(f"{PREFIX}/ai-builder/sessions/{sid}/summary")
    assert summary.status == 200

    create = await client.post(f"{PREFIX}/ai-builder/sessions/{sid}/create", json={})
    assert create.status == 201
    created = await create.json()
    assert created["created_count"] == 1

    registry = await client.get(f"{PREFIX}/ai-builder/registry")
    assert registry.status == 200
    assert (await registry.json())["count"] >= 1

    group = await client.get(f"{PREFIX}/ai-builder/group-chat")
    assert group.status == 200
    assert (await group.json())["status"] == "foundation"


def test_docs_and_frontend_28_2():
    assert (ROOT / "docs" / "AI_BUILDER.md").exists()
    assert (ROOT / "knowledge" / "platform_builder" / "ai_builder" / "README.md").exists()
    assert (ROOT / "applications" / "platform_builder" / "ai_builder" / "wizard.py").exists()
    assert (ROOT / "src" / "web" / "platform-builder" / "ai-builder" / "AIBuilderWizard.tsx").exists()
    docs = (ROOT / "docs" / "AI_BUILDER.md").read_text()
    for key in ("Personality", "Knowledge", "AI Registry", "Group AI Chat"):
        assert key in docs
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.16.0"' in manifest
    assert "29.9" in manifest
