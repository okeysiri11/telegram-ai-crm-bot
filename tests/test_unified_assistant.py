"""Tests — Unified AI Assistant & Global Knowledge (Sprint 7.3)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from ecosystem import ecosystem
from ecosystem.api.register import register_ecosystem_routes
from ecosystem.assistant.models import SkillType
from ecosystem.config import DEFAULT_CONFIG


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_ecosystem_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    ecosystem.reset()
    DEFAULT_CONFIG.registered_applications[:] = ["auto_marketplace"]
    yield
    ecosystem.reset()
    DEFAULT_CONFIG.registered_applications[:] = ["auto_marketplace"]


def test_assistant_version():
    assert DEFAULT_CONFIG.ecosystem_version == "1.4.0-alpha"
    assert DEFAULT_CONFIG.assistant_layer == "1.0"
    assert DEFAULT_CONFIG.global_knowledge == "1.0"


@pytest.mark.asyncio
async def test_invoke_and_conversation():
    result = await ecosystem.engine.assistant.invoke(
        "user-1",
        "Find electric SUVs under 40k",
        application_id="auto_marketplace",
    )
    assert result["reply"]
    assert result["conversation_id"]
    assert result["session_id"] == result["conversation_id"]
    assert result["intent"]
    assert "routing" in result

    conversations = ecosystem.engine.assistant.conversations.list_for_user("user-1")
    assert len(conversations) == 1
    assert len(conversations[0].turns) >= 2


@pytest.mark.asyncio
async def test_knowledge_graph_and_search():
    kg = ecosystem.engine.assistant.knowledge
    a = await kg.upsert_node("EV incentives", "Federal EV tax credit", application_id="auto_marketplace", tags=["ev"])
    b = await kg.upsert_node("SUV segment", "Popular family vehicles", application_id="auto_marketplace", tags=["suv"])
    edge = kg.link(a.node_id, b.node_id, relation="related_to")
    assert edge.relation == "related_to"

    hits = kg.semantic_search("electric tax credit", application_id="auto_marketplace")
    assert hits
    assert hits[0]["node"]["label"] == "EV incentives"

    related = kg.discover_relationships(a.node_id)
    assert related
    synced = await kg.synchronize("auto_marketplace", [{"label": "Warranty", "content": "3 years"}])
    assert len(synced) == 1


@pytest.mark.asyncio
async def test_global_memory_and_context():
    await ecosystem.engine.assistant.memory.remember("user-2", "Prefers EVs", application_id="auto_marketplace", tags=["pref"])
    memories = ecosystem.engine.assistant.memory.recall("user-2", query="EV")
    assert len(memories) == 1

    ctx = ecosystem.engine.assistant.context
    ctx.update(
        "user-2",
        user_context={"locale": "en"},
        application_context={"application_id": "auto_marketplace"},
        organization_context={"organization_id": "org-1"},
        task_context={"goal": "buy car"},
    )
    assembled = ctx.assemble("user-2")
    assert assembled["user"]["locale"] == "en"
    assert assembled["application"]["application_id"] == "auto_marketplace"

    result = await ecosystem.engine.assistant.invoke("user-2", "Remind me of my preferences", application_id="auto_marketplace")
    await ecosystem.engine.assistant.context.restore("user-2", result["conversation_id"])


@pytest.mark.asyncio
async def test_skills_and_routing():
    skills = ecosystem.engine.assistant.skills
    listed = skills.list_skills()
    assert len(listed) >= 4

    custom = skills.register("custom_lookup", skill_type=SkillType.TOOL, description="Custom tool", priority=5)
    executed = await skills.execute(custom.skill_id, "user-3", {"query": "test"})
    assert executed["status"] == "ok"

    decision = await ecosystem.engine.assistant.router.route(
        "user-3",
        "search vehicles in marketplace",
        application_id="auto_marketplace",
    )
    assert decision.intent_label
    assert decision.decision_id


@pytest.mark.asyncio
async def test_task_planning_and_orchestration():
    plan = ecosystem.engine.assistant.plan_task("user-4", "Qualify lead and send offer")
    assert plan.plan_id
    assert len(plan.steps) >= 3

    parts = ecosystem.engine.assistant.decompose_task("Analyze lead. Draft offer. Notify dealer")
    assert len(parts) == 3

    orchestrated = await ecosystem.engine.assistant.orchestrate(
        "user-4",
        "Qualify lead",
        agents=["sales-agent"],
    )
    assert orchestrated["plan"]
    assert orchestrated["agent_results"]


@pytest.mark.asyncio
async def test_conversation_features():
    conv = await ecosystem.engine.assistant.conversations.create("user-5", title="Support", voice_ready=True, locale="en")
    ecosystem.engine.assistant.conversations.append_turn(conv.conversation_id, "user", "Hello")
    ecosystem.engine.assistant.conversations.append_turn(conv.conversation_id, "assistant", "Hi there")
    summarized = ecosystem.engine.assistant.conversations.summarize(conv.conversation_id)
    assert summarized.summary

    translated = ecosystem.engine.assistant.conversations.translate("hello", target_locale="ru")
    assert translated["locale"] == "ru"

    voice = ecosystem.engine.assistant.conversations.voice_payload(conv.conversation_id, "Welcome")
    assert voice["voice_ready"] is True
    assert "ssml" in voice


@pytest.mark.asyncio
async def test_assistant_api(client: TestClient):
    resp = await client.get("/api/ecosystem/v1/health")
    assert resp.status == 200
    health = await resp.json()
    assert health["ecosystem_version"] == "1.4.0-alpha"
    assert health["assistant_layer"] == "1.0"
    assert health["global_knowledge"] == "1.0"

    resp = await client.post(
        "/api/ecosystem/v1/knowledge",
        json={"label": "Deal stages", "content": "Lead to won", "application_id": "auto_marketplace"},
    )
    assert resp.status == 201

    resp = await client.get("/api/ecosystem/v1/knowledge/search?q=deal")
    assert resp.status == 200
    search = await resp.json()
    assert search["hits"]

    resp = await client.post(
        "/api/ecosystem/v1/assistant/invoke",
        json={"user_id": "api-user", "message": "Explain deal stages", "application_id": "auto_marketplace"},
    )
    assert resp.status == 200
    payload = await resp.json()
    assert payload["reply"]
    assert payload["conversation_id"]

    resp = await client.get("/api/ecosystem/v1/skills")
    assert resp.status == 200
    skills = await resp.json()
    assert skills["skills"]

    resp = await client.post(
        "/api/ecosystem/v1/context",
        json={"user_id": "api-user", "user_context": {"locale": "en"}},
    )
    assert resp.status == 200

    resp = await client.get("/api/ecosystem/v1/manifest")
    assert resp.status == 200
    manifest = await resp.json()
    assert manifest["ecosystem_version"] == "1.4.0-alpha"
    assert manifest["assistant_layer"] == "1.0"
    assert manifest["global_knowledge"] == "1.0"
