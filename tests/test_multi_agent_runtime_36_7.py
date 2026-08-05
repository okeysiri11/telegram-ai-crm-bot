"""Tests — Multi-Agent Runtime (Sprint 36.7)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_management.permissions import ManagementRole
from platform_orchestrator.multi_agent_router import register_multi_agent_runtime_routes
from platform_orchestrator.multi_agent_service import multi_agent_runtime_service as mars
from platform_orchestrator.runtime_models import CollaborationMode


@pytest.fixture
def engine():
    mars.reset()
    mars.ensure_ready()
    yield mars
    mars.reset()


def test_agent_registry(engine):
    agents = engine.list_agents()
    assert len(agents) >= 5
    ids = {a["agent_id"] for a in agents}
    assert "agent_planner" in ids
    assert "agent_supervisor" in ids
    rec = engine.register_agent(
        {
            "name": "Custom Analyst",
            "capabilities": ["analyze"],
            "skills": ["research"],
            "permissions": ["agent.execute"],
        }
    )
    assert rec["agent_id"]
    assert engine.get_agent(rec["agent_id"])["name"] == "Custom Analyst"
    health = engine.health()
    assert health and all("healthy" in h for h in health)


@pytest.mark.asyncio
async def test_collaboration_modes(engine):
    for mode in CollaborationMode:
        result = await engine.orchestrate({"goal": f"goal for {mode.value}", "mode": mode.value})
        assert result["execution"]["status"] == "completed"
        assert result["aggregated"]["mode"] == mode.value
        assert result["aggregated"]["steps_total"] >= 1
        assert result["task_graph"]["node_count"] >= 1


@pytest.mark.asyncio
async def test_communication_shared_memory(engine):
    session = engine.create_session({"goal": "share", "mode": "parallel"})
    engine.update_shared(session["session_id"], {"shared_context": {"k": 1}, "shared_memory": {"m": 2}})
    updated = engine.get_session(session["session_id"])
    assert updated["shared_context"]["k"] == 1
    assert updated["shared_memory"]["m"] == 2

    direct = await engine.send_message(
        {
            "channel": "direct",
            "from": "agent_planner",
            "to": "agent_worker",
            "payload": {"hello": True},
        }
    )
    assert direct["channel"] == "direct"

    engine.subscribe({"agent_id": "agent_worker", "topic": "ops"})
    pub = await engine.send_message(
        {"channel": "pubsub", "topic": "ops", "source_agent_id": "agent_supervisor", "payload": {"ping": 1}}
    )
    assert pub["count"] >= 1
    assert engine.list_messages()


@pytest.mark.asyncio
async def test_task_runtime_controls(engine):
    task = engine.enqueue_task({"title": "do work", "capability": "work", "agent_id": "agent_worker"})
    assert task["status"] == "queued"
    engine.checkpoint_task(task["task_id"], {"checkpoint": {"progress": 50}})
    cp = engine.get_task(task["task_id"])
    assert cp["status"] == "checkpointed"
    assert cp["checkpoint"]["progress"] == 50

    task2 = engine.enqueue_task({"title": "cancel me", "capability": "work"})
    cancelled = engine.cancel_task(task2["task_id"])
    assert cancelled["status"] == "cancelled"

    task3 = engine.enqueue_task({"title": "run me", "capability": "buy_car", "max_retries": 1, "timeout_sec": 10})
    done = await engine.run_task(task3["task_id"])
    assert done["status"] in ("completed", "failed", "timeout")


@pytest.mark.asyncio
async def test_planner_and_graph(engine):
    plan = engine.plan({"goal": "ship feature", "mode": "hierarchical"})
    assert plan["plan_id"]
    assert len(plan["steps"]) >= 2
    g = engine.task_graph(plan["plan_id"])
    assert g["node_count"] >= 2
    assert engine.list_plans()


@pytest.mark.asyncio
async def test_integrations(engine):
    from platform_ai.service import ai_runtime_service
    from platform_service_builder.service import service_builder
    from platform_workflow.service import workflow_runtime_service as wrs

    ai_runtime_service.reset()
    wrs.reset()
    wrs.ensure_seed()
    service_builder.reset()
    service_builder.ensure_seed()

    ai = await engine.for_ai_runtime({"goal": "coordinate launch", "mode": "parallel"})
    assert ai["consumer"] == "ai_runtime"
    assert ai["execution"]["status"] == "completed"

    mem = await engine.for_project_memory({"goal": "remember collab"})
    assert mem["consumer"] == "project_memory"
    assert mem["session"]["session_id"]

    ctx = await engine.for_context_engine({"goal": "context collab"})
    assert ctx["consumer"] == "context_engine"

    wf = await engine.for_workflow({"goal": "workflow collab", "mode": "sequential"})
    assert wf["consumer"] == "workflow"

    sb = await engine.for_service_builder({})
    assert sb["service_id"] == "svc_multi_agent_runtime"

    voice = await engine.for_voice({"transcript": "call ai agent to help", "mode": "supervisor_worker"})
    assert voice["consumer"] == "voice_runtime"

    ai_runtime_service.reset()
    wrs.reset()
    service_builder.reset()


@pytest.mark.asyncio
async def test_rest_api(engine, auth_headers, monkeypatch):
    async def _admin(_tid):
        return ManagementRole.ADMINISTRATOR

    monkeypatch.setattr("platform_management.permissions.resolve_role", _admin)
    app = web.Application()
    register_multi_agent_runtime_routes(app)

    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            res = await client.get("/api/agents/agents", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 5

            res = await client.post(
                "/api/multi-agent/orchestrate",
                headers=auth_headers,
                json={"goal": "api orchestrate", "mode": "swarm"},
            )
            assert res.status == 200
            assert (await res.json())["data"]["execution"]["status"] == "completed"

            res = await client.get("/api/multi-agent/statistics", headers=auth_headers)
            assert res.status == 200

            res = await client.get("/management/v1/agents/status", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["sprint"] == "36.7"

    mars.reset()


def test_ui_present():
    page = Path(__file__).resolve().parents[1] / "src/web/src/multi-agent-console/MultiAgentRuntimePage.tsx"
    text = page.read_text(encoding="utf-8")
    for label in (
        "Agent Dashboard",
        "Live Execution",
        "Task Graph",
        "Planner",
        "Communication",
        "Statistics",
    ):
        assert label in text


def test_orm_and_migration():
    from database.models.multi_agent import (
        AgentExecutionRow,
        AgentMessageRow,
        AgentPlanRow,
        AgentRegistryRow,
        AgentSessionRow,
        AgentStatisticsRow,
        AgentTaskRow,
    )

    assert AgentRegistryRow.__tablename__ == "agent_registry"
    assert AgentTaskRow.__tablename__ == "agent_tasks"
    assert AgentMessageRow.__tablename__ == "agent_messages"
    assert AgentSessionRow.__tablename__ == "agent_sessions"
    assert AgentPlanRow.__tablename__ == "agent_plans"
    assert AgentExecutionRow.__tablename__ == "agent_execution"
    assert AgentStatisticsRow.__tablename__ == "agent_statistics"

    mig = Path(__file__).resolve().parents[1] / "migrations/versions/q0k123456789_multi_agent_runtime_v1.py"
    text = mig.read_text(encoding="utf-8")
    for table in (
        "agent_registry",
        "agent_tasks",
        "agent_messages",
        "agent_sessions",
        "agent_plans",
        "agent_execution",
        "agent_statistics",
    ):
        assert table in text


def test_exports():
    from platform_orchestrator import (
        CollaborationMode,
        MultiAgentRuntimeEngine,
        MultiAgentRuntimeService,
        multi_agent_runtime_engine,
        multi_agent_runtime_service,
    )

    assert CollaborationMode.SWARM
    assert MultiAgentRuntimeEngine and MultiAgentRuntimeService
    assert multi_agent_runtime_engine and multi_agent_runtime_service
