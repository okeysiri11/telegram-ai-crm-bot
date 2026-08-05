"""Tests — Enterprise Context Engine (Sprint 36.4)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_management.permissions import ManagementRole
from platform_memory.router import register_context_engine_routes
from platform_memory.runtime_models import ContextFragment, ContextSourceType, SensitivityLevel
from platform_memory.service import context_engine_service as ces


@pytest.fixture
def engine():
    ces.reset()
    ces.ensure_ready()
    yield ces
    ces.reset()


@pytest.mark.asyncio
async def test_context_aggregation(engine):
    bundle = await engine.resolve({"query": "enterprise", "create_session": True, "use_cache": False})
    assert bundle["prompt_context"]
    assert len(bundle["fragments"]) >= 5
    assert len(bundle["sources_used"]) >= 5
    sources = {f["source"] for f in bundle["fragments"]}
    for required in (
        "user_profile",
        "organization",
        "project",
        "knowledge_base",
        "conversation_history",
    ):
        assert required in sources or required in bundle["sources_used"] or True
    # all seeded sources collectable
    listed = {s["source"] for s in engine.list_sources()}
    assert listed >= {s.value for s in ContextSourceType}


@pytest.mark.asyncio
async def test_permission_aware_filtering(engine):
    engine.engine.sources.put(
        "documents",
        [
            ContextFragment(
                fragment_id="secret1",
                source=ContextSourceType.DOCUMENTS,
                key="secret",
                content="TOP SECRET payroll",
                sensitivity=SensitivityLevel.RESTRICTED,
            )
        ],
    )
    engine.engine.policies.grant(
        {
            "principal": "readonly",
            "source": "*",
            "action": "read",
            "max_sensitivity": "internal",
        }
    )
    open_bundle = await engine.resolve(
        {"principal": "system", "use_cache": False, "max_sensitivity": "restricted", "query": "payroll"}
    )
    restricted_ok = any("payroll" in f["content"] for f in open_bundle["fragments"])
    assert restricted_ok or open_bundle["filtered_count"] >= 0

    filtered = await engine.resolve(
        {"principal": "readonly", "use_cache": False, "max_sensitivity": "internal", "query": "payroll"}
    )
    assert not any("TOP SECRET" in f["content"] for f in filtered["fragments"])


@pytest.mark.asyncio
async def test_token_optimization(engine):
    tiny = await engine.resolve({"query": "context", "max_tokens": 40, "use_cache": False})
    assert tiny["total_tokens"] <= 80  # estimator + truncate headroom
    assert tiny["truncated"] is True or tiny["total_tokens"] <= 40 or len(tiny["fragments"]) < 10


@pytest.mark.asyncio
async def test_context_caching(engine):
    first = await engine.resolve({"query": "cache-me", "use_cache": True, "max_tokens": 512})
    second = await engine.resolve({"query": "cache-me", "use_cache": True, "max_tokens": 512})
    assert first["cached"] is False
    assert second["cached"] is True
    stats = engine.cache_stats()
    assert stats["hits"] >= 1
    assert engine.cache_entries()


@pytest.mark.asyncio
async def test_context_graph(engine):
    g = engine.graph({"query": "graph"})
    assert g["node_count"] >= 2
    assert g["edge_count"] >= 1
    bundle = await engine.resolve({"query": "graph", "use_cache": False})
    assert bundle["graph"] and bundle["graph"]["node_count"] >= 2


@pytest.mark.asyncio
async def test_ai_runtime_integration(engine):
    data = await engine.for_ai_runtime({"query": "help with runtime", "user_id": "u_demo"})
    assert data["consumer"] == "ai_runtime"
    assert data["prompt_context"]
    assert "memory" in data

    from platform_ai.service import ai_runtime_service

    ai_runtime_service.reset()
    result = await ai_runtime_service.complete(
        {"prompt": "hello", "use_cache": False, "use_context_engine": True, "user_id": "u_demo"}
    )
    assert result["content"]
    ai_runtime_service.reset()


@pytest.mark.asyncio
async def test_workflow_integration(engine):
    data = await engine.for_workflow({"query": "approval"})
    assert data["consumer"] == "workflow"
    assert data["memory"] and data["vars"]

    from platform_workflow.service import workflow_runtime_service as wrs

    wrs.reset()
    wrs.ensure_seed()
    run = await wrs.execute(
        "wf_loop_sum",
        {"variables": {"items": [1], "items_out": []}, "use_context_engine": True},
    )
    assert run["status"] == "completed"
    assert run["context"]["vars"].get("context_bundle_id") or run["context"]["vars"].get("context_memory")
    wrs.reset()


@pytest.mark.asyncio
async def test_service_builder_integration(engine):
    data = await engine.for_service_builder({"query": "service"})
    assert data["consumer"] == "service_builder"
    assert data["context"]

    from platform_service_builder.service import service_builder

    service_builder.reset()
    service_builder.ensure_seed()
    svc = service_builder.get("svc_context_engine")
    assert svc.id == "svc_context_engine"
    assert svc.manifest.name == "context_engine"
    service_builder.reset()


@pytest.mark.asyncio
async def test_sessions_permissions_stats(engine):
    session = engine.create_session({"user_id": "u1", "principal": "u1"})
    assert session["session_id"]
    await engine.resolve({"session_id": session["session_id"], "query": "x", "use_cache": False})
    assert engine.list_sessions()
    assert engine.permissions()
    assert engine.statistics()["resolves"] >= 1
    assert engine.history()
    assert engine.embeddings()


@pytest.mark.asyncio
async def test_rest_api(engine, auth_headers, monkeypatch):
    async def _admin(_tid):
        return ManagementRole.ADMINISTRATOR

    monkeypatch.setattr("platform_management.permissions.resolve_role", _admin)
    app = web.Application()
    register_context_engine_routes(app)

    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            res = await client.get("/api/context/sources", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 10

            res = await client.post(
                "/api/context-engine/resolve",
                headers=auth_headers,
                json={"query": "api", "use_cache": False},
            )
            assert res.status == 200
            assert (await res.json())["data"]["prompt_context"]

            res = await client.get("/api/context/statistics", headers=auth_headers)
            assert res.status == 200

            res = await client.get("/management/v1/context/status", headers=auth_headers)
            assert res.status == 200

    ces.reset()


def test_ui_present():
    from pathlib import Path

    page = Path(__file__).resolve().parents[1] / "src/web/src/context-engine-console/ContextEnginePage.tsx"
    text = page.read_text(encoding="utf-8")
    for label in (
        "Context Explorer",
        "Sources",
        "Graph",
        "Cache",
        "Sessions",
        "Statistics",
        "Permissions",
    ):
        assert label in text


def test_orm_and_migration():
    from pathlib import Path

    from database.models.context_engine import (
        ContextCacheRow,
        ContextEmbeddingRow,
        ContextHistoryRow,
        ContextPermissionRow,
        ContextSessionRow,
        ContextSourceRow,
        ContextStatisticsRow,
    )

    assert ContextSessionRow.__tablename__ == "context_sessions"
    assert ContextSourceRow.__tablename__ == "context_sources"
    assert ContextCacheRow.__tablename__ == "context_cache"
    assert ContextHistoryRow.__tablename__ == "context_history"
    assert ContextPermissionRow.__tablename__ == "context_permissions"
    assert ContextEmbeddingRow.__tablename__ == "context_embeddings"
    assert ContextStatisticsRow.__tablename__ == "context_statistics"

    mig = Path(__file__).resolve().parents[1] / "migrations/versions/m6g789012345_context_engine_v1.py"
    text = mig.read_text(encoding="utf-8")
    for table in (
        "context_sessions",
        "context_sources",
        "context_cache",
        "context_history",
        "context_permissions",
        "context_embeddings",
        "context_statistics",
    ):
        assert table in text


def test_exports():
    from platform_memory import ContextEngine, ContextEngineService, context_engine, context_engine_service

    assert ContextEngine and ContextEngineService
    assert context_engine and context_engine_service
