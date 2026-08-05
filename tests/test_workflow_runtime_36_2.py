"""Tests — Workflow Runtime (Sprint 36.2)."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_management.permissions import ManagementRole
from platform_workflow.router import register_workflow_runtime_routes
from platform_workflow.runtime_models import RegistryStatus, RunStatus
from platform_workflow.service import workflow_runtime_service as wrs


@pytest.fixture
def runtime():
    wrs.reset()
    wrs.ensure_seed()
    yield wrs
    wrs.reset()


@pytest.mark.asyncio
async def test_registry_versioning(runtime):
    wf = runtime.register(
        {
            "workflow_id": "wf_custom",
            "name": "Custom",
            "version": "1.0.0",
            "steps": [
                {"step_id": "start", "name": "Start", "kind": "start", "next": ["end"]},
                {"step_id": "end", "name": "End", "kind": "end"},
            ],
        }
    )
    assert wf["status"] == "draft"
    published = runtime.publish("wf_custom")
    assert published["status"] == "published"
    runtime.update_workflow("wf_custom", {"version": "1.1.0", "changelog": "bump"})
    versions = runtime.versions("wf_custom")
    assert any(v["version"] == "1.1.0" and v["is_active"] for v in versions)
    archived = runtime.archive("wf_custom")
    assert archived["status"] == "archived"


@pytest.mark.asyncio
async def test_condition_and_parallel(runtime):
    run = await runtime.execute("wf_approval_pipeline", {"variables": {"amount": 1000}})
    assert run["status"] == "completed"
    step_ids = [s["step_id"] for s in run["steps"]]
    assert "check" in step_ids
    assert "parallel_review" in step_ids
    assert "rev_a" in step_ids and "rev_b" in step_ids
    assert "finalize" in step_ids
    assert run["context"]["vars"].get("done") is True


@pytest.mark.asyncio
async def test_condition_false_branch(runtime):
    run = await runtime.execute("wf_approval_pipeline", {"variables": {"amount": 10}})
    assert run["status"] == "completed"
    step_ids = [s["step_id"] for s in run["steps"]]
    assert "auto_approve" in step_ids
    assert "parallel_review" not in step_ids


@pytest.mark.asyncio
async def test_loop(runtime):
    run = await runtime.execute("wf_loop_sum", {"variables": {"items": [1, 2, 3], "items_out": []}})
    assert run["status"] == "completed"
    assert run["context"]["vars"]["items_out"] == [1, 2, 3]


@pytest.mark.asyncio
async def test_retry_on_step_failure(runtime):
    runtime.register(
        {
            "workflow_id": "wf_flaky",
            "name": "Flaky",
            "version": "1.0.0",
            "steps": [
                {"step_id": "start", "name": "Start", "kind": "start", "next": ["boom"]},
                {
                    "step_id": "boom",
                    "name": "Boom",
                    "kind": "task",
                    "action": "fail",
                    "max_retries": 2,
                    "metadata": {"error": "nope"},
                    "next": ["end"],
                },
                {"step_id": "end", "name": "End", "kind": "end"},
            ],
        }
    )
    run = await runtime.execute("wf_flaky", {})
    assert run["status"] == "failed"
    boom = next(s for s in run["steps"] if s["step_id"] == "boom")
    assert boom["attempt"] == 3  # initial + 2 retries


@pytest.mark.asyncio
async def test_rollback(runtime):
    runtime.register(
        {
            "workflow_id": "wf_rb",
            "name": "Rollbackable",
            "version": "1.0.0",
            "steps": [
                {"step_id": "start", "name": "Start", "kind": "start", "next": ["work"]},
                {
                    "step_id": "work",
                    "name": "Work",
                    "kind": "task",
                    "action": "set_variable",
                    "set_var": "flag",
                    "value": 1,
                    "compensate": "undo",
                    "next": ["end"],
                },
                {"step_id": "undo", "name": "Undo", "kind": "task", "action": "echo", "metadata": {"message": "undone"}},
                {"step_id": "end", "name": "End", "kind": "end"},
            ],
        }
    )
    # fix: set_variable kind
    runtime.update_workflow(
        "wf_rb",
        {
            "steps": [
                {"step_id": "start", "name": "Start", "kind": "start", "next": ["work"]},
                {
                    "step_id": "work",
                    "name": "Work",
                    "kind": "set_variable",
                    "set_var": "flag",
                    "value": 1,
                    "compensate": "undo",
                    "next": ["end"],
                },
                {"step_id": "undo", "name": "Undo", "kind": "task", "action": "echo", "metadata": {"message": "undone"}},
                {"step_id": "end", "name": "End", "kind": "end"},
            ]
        },
    )
    run = await runtime.execute("wf_rb", {})
    assert run["status"] == "completed"
    rb = await runtime.rollback(run["run_id"])
    assert rb["status"] == "rolled_back"
    assert any(s["step_id"] == "undo" for s in rb["steps"])


@pytest.mark.asyncio
async def test_scheduler(runtime):
    future = time.time() + 3600
    run = await runtime.execute(
        "wf_loop_sum",
        {"variables": {"items": [9], "items_out": []}, "schedule_at": future},
    )
    assert run["status"] == "scheduled"
    # force due
    runtime.runtime._scheduled[0].scheduled_at = time.time() - 1
    tick = await runtime.process_scheduled()
    assert tick["processed"] == 1
    updated = runtime.get_run(run["run_id"])
    assert updated["status"] == "completed"


@pytest.mark.asyncio
async def test_async_execution(runtime):
    run = await runtime.execute("wf_loop_sum", {"variables": {"items": [1], "items_out": []}, "mode": "async"})
    # allow task to finish
    import asyncio

    for _ in range(50):
        current = runtime.get_run(run["run_id"])
        if current["status"] in {"completed", "failed", "cancelled"}:
            break
        await asyncio.sleep(0.02)
    assert runtime.get_run(run["run_id"])["status"] == "completed"


@pytest.mark.asyncio
async def test_execution_history_and_checkpoints(runtime):
    run = await runtime.execute("wf_approval_pipeline", {"variables": {"amount": 10}})
    assert run["logs"]
    assert run["checkpoints"]
    assert len(runtime.list_runs()) >= 1


@pytest.mark.asyncio
async def test_api_routes(auth_headers, monkeypatch):
    wrs.reset()
    wrs.ensure_seed()

    async def _admin(_tid):
        return ManagementRole.ADMINISTRATOR

    monkeypatch.setattr("platform_management.permissions.resolve_role", _admin)
    app = web.Application()
    register_workflow_runtime_routes(app)

    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            res = await client.get("/api/workflows/workflows", headers=auth_headers)
            assert res.status == 200
            assert (await res.json())["data"]["count"] >= 2

            res = await client.post(
                "/api/workflows/workflows/wf_loop_sum/execute",
                headers=auth_headers,
                json={"variables": {"items": [1, 2], "items_out": []}},
            )
            assert res.status == 200
            body = await res.json()
            assert body["data"]["status"] == "completed"

            res = await client.get("/api/workflow-runtime/runs", headers=auth_headers)
            assert res.status == 200

            res = await client.get("/api/workflows/monitoring", headers=auth_headers)
            assert res.status == 200

            res = await client.get("/management/v1/workflows/workflows", headers=auth_headers)
            assert res.status == 200

    wrs.reset()


def test_ui_present():
    from pathlib import Path

    page = Path(__file__).resolve().parents[1] / "src/web/src/workflow-runtime-console/WorkflowRuntimePage.tsx"
    text = page.read_text(encoding="utf-8")
    for label in ("Designer", "Runtime", "Executions", "Logs", "Variables", "Versions", "Scheduler", "Monitoring"):
        assert label in text


def test_orm_tables():
    from database.models.workflow_runtime import (
        WorkflowCheckpointRow,
        WorkflowLogRow,
        WorkflowRegistryRow,
        WorkflowRunRow,
        WorkflowStepRow,
        WorkflowVariableRow,
        WorkflowVersionRow,
    )

    assert WorkflowRegistryRow.__tablename__ == "workflow_registry"
    assert WorkflowVersionRow.__tablename__ == "workflow_versions"
    assert WorkflowRunRow.__tablename__ == "workflow_runs"
    assert WorkflowStepRow.__tablename__ == "workflow_steps"
    assert WorkflowVariableRow.__tablename__ == "workflow_variables"
    assert WorkflowLogRow.__tablename__ == "workflow_logs"
    assert WorkflowCheckpointRow.__tablename__ == "workflow_checkpoints"


def test_exports():
    from platform_workflow import (
        WorkflowRegistry,
        WorkflowRuntimeEngine,
        WorkflowRuntimeService,
        workflow_registry,
        workflow_runtime,
        workflow_runtime_service,
    )

    assert WorkflowRegistry and WorkflowRuntimeEngine and WorkflowRuntimeService
    assert workflow_registry and workflow_runtime and workflow_runtime_service
