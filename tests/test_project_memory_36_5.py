"""Tests — Project Memory Engine (Sprint 36.5)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_management.permissions import ManagementRole
from platform_memory.project_memory_models import MemoryKind, MemoryLayer
from platform_memory.project_memory_router import register_project_memory_routes
from platform_memory.project_memory_service import project_memory_service as pms


@pytest.fixture
def engine():
    pms.reset()
    pms.ensure_ready()
    yield pms
    pms.reset()


@pytest.mark.asyncio
async def test_memory_registry(engine):
    kinds = {m["kind"] for m in engine.list_memories()}
    assert kinds >= {
        MemoryKind.PROJECT.value,
        MemoryKind.AGENT.value,
        MemoryKind.CLIENT.value,
        MemoryKind.WORKFLOW.value,
        MemoryKind.DOCUMENT.value,
    }
    rec = await engine.remember(
        {
            "kind": "agent",
            "layer": "working",
            "title": "Test note",
            "content": "Agent wrote this memory for sprint 36.5.",
            "agent_id": "agent_test",
            "project_id": "proj_ados",
        }
    )
    assert rec["memory_id"]
    assert engine.get(rec["memory_id"])["title"] == "Test note"
    assert engine.chunks(rec["memory_id"])


@pytest.mark.asyncio
async def test_memory_layers(engine):
    layers = {m["layer"] for m in engine.list_memories()}
    assert layers >= {
        MemoryLayer.SHORT_TERM.value,
        MemoryLayer.WORKING.value,
        MemoryLayer.LONG_TERM.value,
        MemoryLayer.SHARED_TEAM.value,
    }
    short = await engine.remember(
        {
            "kind": "workflow",
            "layer": "short_term",
            "title": "TTL check",
            "content": "expires soon",
            "workflow_id": "wf_tmp",
        }
    )
    assert short["expires_at"] is not None


@pytest.mark.asyncio
async def test_semantic_search(engine):
    hits = await engine.search({"query": "Project Memory Engine semantic", "limit": 5})
    assert hits["count"] >= 1
    assert hits["hits"][0]["score"] > 0
    assert "memory_id" in hits["hits"][0]


@pytest.mark.asyncio
async def test_relations_sessions_timeline_feedback(engine):
    mems = engine.list_memories()
    assert len(mems) >= 2
    rel = engine.link({"from_id": mems[0]["memory_id"], "to_id": mems[1]["memory_id"], "relation": "related"})
    assert rel["relation_id"]
    g = engine.graph()
    assert g["node_count"] >= 2
    assert g["edge_count"] >= 1

    session = engine.create_session({"project_id": "proj_ados", "agent_id": "agent_test"})
    pinned = engine.pin(session["session_id"], mems[0]["memory_id"])
    assert mems[0]["memory_id"] in pinned["working_set"]
    assert engine.list_sessions()
    assert engine.timeline()
    fb = engine.feedback({"memory_id": mems[0]["memory_id"], "score": 1.0, "comment": "useful"})
    assert fb["feedback_id"]
    assert engine.analytics()["memories"] >= 5


@pytest.mark.asyncio
async def test_ai_runtime_integration(engine):
    data = await engine.for_ai_runtime({"query": "architecture platform_memory", "project_id": "proj_ados"})
    assert data["consumer"] == "ai_runtime"
    assert data["prompt_context"]

    from platform_ai.service import ai_runtime_service

    ai_runtime_service.reset()
    result = await ai_runtime_service.complete(
        {
            "prompt": "hello memory",
            "use_cache": False,
            "use_project_memory": True,
            "project_id": "proj_ados",
            "agent_id": "agent_orchestrator",
        }
    )
    assert result["content"]
    ai_runtime_service.reset()


@pytest.mark.asyncio
async def test_context_engine_integration(engine):
    data = await engine.for_context_engine({"query": "sprint", "project_id": "proj_ados"})
    assert data["consumer"] == "context_engine"
    assert data["fragments"]

    from platform_memory.service import context_engine_service

    context_engine_service.reset()
    ctx = await context_engine_service.for_ai_runtime(
        {"query": "memory", "use_project_memory": True, "project_id": "proj_ados"}
    )
    assert ctx["prompt_context"]
    assert ctx.get("project_memory")
    context_engine_service.reset()


@pytest.mark.asyncio
async def test_workflow_integration(engine):
    data = await engine.for_workflow(
        {"query": "approval", "workflow_id": "wf_approval_pipeline", "project_id": "proj_ados"}
    )
    assert data["consumer"] == "workflow"
    assert data["hits"] or data["memory"]

    from platform_workflow.service import workflow_runtime_service as wrs

    wrs.reset()
    wrs.ensure_seed()
    run = await wrs.execute(
        "wf_loop_sum",
        {"variables": {"items": [1], "items_out": []}, "use_project_memory": True, "project_id": "proj_ados"},
    )
    assert run["status"] == "completed"
    assert run["context"]["vars"].get("project_memory") is not None or run["context"]["vars"].get(
        "project_memory_hits"
    ) is not None
    wrs.reset()


@pytest.mark.asyncio
async def test_service_builder_integration(engine):
    data = await engine.for_service_builder({"query": "memory"})
    assert data["consumer"] == "service_builder"

    from platform_service_builder.service import service_builder

    service_builder.reset()
    service_builder.ensure_seed()
    svc = service_builder.get("svc_project_memory")
    assert svc.id == "svc_project_memory"
    assert svc.manifest.name == "project_memory"
    service_builder.reset()


@pytest.mark.asyncio
async def test_agent_read_write(engine):
    written = await engine.remember(
        {
            "kind": "agent",
            "layer": "working",
            "title": "RW",
            "content": "agent read write",
            "agent_id": "agent_rw",
        }
    )
    listed = engine.list_memories(agent_id="agent_rw")
    assert any(m["memory_id"] == written["memory_id"] for m in listed)


@pytest.mark.asyncio
async def test_rest_api(engine, auth_headers, monkeypatch):
    async def _admin(_tid):
        return ManagementRole.ADMINISTRATOR

    monkeypatch.setattr("platform_management.permissions.resolve_role", _admin)
    app = web.Application()
    register_project_memory_routes(app)

    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            res = await client.get("/api/project-memory/memories", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 5

            res = await client.post(
                "/api/memory/search",
                headers=auth_headers,
                json={"query": "Project Memory", "limit": 5},
            )
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 1

            res = await client.get("/api/project-memory/analytics", headers=auth_headers)
            assert res.status == 200

            res = await client.get("/management/v1/project-memory/status", headers=auth_headers)
            assert res.status == 200

            res = await client.post(
                "/api/project-memory/agents/agent_api/remember",
                headers=auth_headers,
                json={"title": "from api", "content": "agent write via REST", "layer": "working"},
            )
            assert res.status == 201

            res = await client.get(
                "/api/project-memory/agents/agent_api/memories",
                headers=auth_headers,
            )
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 1

    pms.reset()


def test_ui_present():
    page = Path(__file__).resolve().parents[1] / "src/web/src/project-memory-console/ProjectMemoryPage.tsx"
    text = page.read_text(encoding="utf-8")
    for label in (
        "Memory Dashboard",
        "Search",
        "Timeline",
        "Relations Graph",
        "Sessions",
        "Analytics",
    ):
        assert label in text


def test_orm_and_migration():
    from database.models.project_memory import (
        MemoryChunkRow,
        MemoryEmbeddingRow,
        MemoryFeedbackRow,
        MemoryHistoryRow,
        MemoryRelationRow,
        MemorySessionRow,
        ProjectMemoryRow,
    )

    assert ProjectMemoryRow.__tablename__ == "project_memory"
    assert MemoryChunkRow.__tablename__ == "memory_chunks"
    assert MemoryEmbeddingRow.__tablename__ == "memory_embeddings"
    assert MemoryRelationRow.__tablename__ == "memory_relations"
    assert MemorySessionRow.__tablename__ == "memory_sessions"
    assert MemoryHistoryRow.__tablename__ == "memory_history"
    assert MemoryFeedbackRow.__tablename__ == "memory_feedback"

    mig = Path(__file__).resolve().parents[1] / "migrations/versions/o8i901234567_project_memory_engine_v1.py"
    text = mig.read_text(encoding="utf-8")
    for table in (
        "project_memory",
        "memory_chunks",
        "memory_embeddings",
        "memory_relations",
        "memory_sessions",
        "memory_history",
        "memory_feedback",
    ):
        assert table in text


def test_exports():
    from platform_memory import (
        ProjectMemoryEngine,
        ProjectMemoryService,
        project_memory_engine,
        project_memory_service,
        MemoryKind,
        MemoryLayer,
    )

    assert ProjectMemoryEngine and ProjectMemoryService
    assert project_memory_engine and project_memory_service
    assert MemoryKind.PROJECT and MemoryLayer.LONG_TERM
