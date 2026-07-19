"""Tests — configurable Workflow Engine."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp.test_utils import TestClient, TestServer

from events.event_bus import reset_subscribers
from events.handlers import reset_handler_registration
from events.workflow_events import (
    WorkflowCompletedEvent,
    WorkflowStartedEvent,
    WorkflowStepCompletedEvent,
)
from workflow.models import ExecutionStatus, StepType
from workflow.workflow_context import WorkflowContext
from workflow.workflow_executor import WorkflowExecutor, evaluate_condition
from workflow.workflow_loader import WorkflowLoader, parse_workflow_document
from workflow.workflow_registry import WorkflowRegistry
from workflow.workflow_validator import WorkflowValidator, WorkflowValidationError
from workflow.workflow_engine import WorkflowEngine


@pytest.fixture(autouse=True)
def _clean_bus():
    reset_subscribers()
    reset_handler_registration()
    yield
    reset_subscribers()
    reset_handler_registration()


@pytest.fixture
def sample_workflow_dict():
    return {
        "workflow": {
            "id": "test_flow",
            "vertical": "AUTO",
            "steps": [
                {"id": "start", "type": "input", "variable": "phone"},
                {
                    "id": "check_vin",
                    "type": "condition",
                    "when": "vin == yes",
                    "then": "vin_step",
                    "else": "done",
                },
                {"id": "vin_step", "type": "question", "variable": "vin_code"},
                {"id": "done", "type": "complete"},
            ],
        }
    }


def test_parse_workflow_json(sample_workflow_dict):
    definition = parse_workflow_document(sample_workflow_dict)
    assert definition.id == "test_flow"
    assert definition.vertical == "AUTO"
    assert len(definition.steps) == 4
    first = definition.first_step()
    assert first is not None
    assert first.type == StepType.INPUT


def test_workflow_validation_success(sample_workflow_dict):
    definition = parse_workflow_document(sample_workflow_dict)
    errors = WorkflowValidator.validate(definition)
    assert errors == []


def test_workflow_validation_missing_complete():
    data = {
        "workflow": {
            "id": "bad",
            "vertical": "AUTO",
            "steps": [{"id": "only", "type": "input"}],
        }
    }
    definition = parse_workflow_document(data)
    errors = WorkflowValidator.validate(definition)
    assert any("complete" in e for e in errors)


def test_workflow_validation_raises():
    data = {
        "workflow": {
            "id": "bad",
            "vertical": "AUTO",
            "steps": [{"id": "only", "type": "input"}],
        }
    }
    with pytest.raises(WorkflowValidationError):
        WorkflowValidator.validate_or_raise(parse_workflow_document(data))


def test_load_yaml_definition():
    path = Path(__file__).resolve().parents[1] / "workflow" / "definitions" / "auto_buy.yaml"
    definition = WorkflowLoader.load_file(path)
    assert definition.id == "auto_buy"
    assert definition.vertical == "AUTO"
    assert any(s.id == "assign_manager" for s in definition.steps.values())


def test_condition_evaluation():
    ctx = WorkflowContext.create(workflow_id="t", vertical="AUTO", variables={"vin": "yes"})
    assert evaluate_condition("vin == yes", ctx) is True
    assert evaluate_condition("vin == no", ctx) is False


def test_registry_load_and_lookup():
    registry = WorkflowRegistry()
    base = Path(__file__).resolve().parents[1] / "workflow" / "definitions"
    count = registry.load_from_directory(base)
    assert count >= 3
    assert registry.get("auto_buy") is not None
    assert registry.get_for_vertical("AGRO") is not None


@pytest.mark.asyncio
async def test_branching_condition_routes_to_else():
    registry = WorkflowRegistry()
    definition = parse_workflow_document(
        {
            "workflow": {
                "id": "branch",
                "vertical": "AUTO",
                "steps": [
                    {
                        "id": "check",
                        "type": "condition",
                        "when": "vin == yes",
                        "then": "vin_step",
                        "else": "done",
                    },
                    {"id": "vin_step", "type": "complete"},
                    {"id": "done", "type": "complete"},
                ],
            }
        }
    )
    registry.register(definition)
    engine = WorkflowEngine(registry)

    ctx = WorkflowContext.create(
        workflow_id="branch",
        vertical="AUTO",
        variables={"vin": "no"},
        current_step="check",
    )
    ctx.status = ExecutionStatus.RUNNING
    ctx.request = {"request_number": "AUTO-0001"}
    engine._active[ctx.execution_id] = ctx

    published: list = []

    async def _capture(event, *, wait=False):
        published.append(event)
        return {"handlers": 0, "errors": []}

    with patch.object(engine, "_persist", new=AsyncMock()), patch.object(
        engine, "_log_step", new=AsyncMock()
    ), patch("platform_workflows.workflow_engine.publish", side_effect=_capture):
        result = await engine._continue_from(ctx, definition, "check")

    assert result.status == ExecutionStatus.COMPLETED
    assert any(isinstance(e, WorkflowStepCompletedEvent) for e in published)


@pytest.mark.asyncio
async def test_context_persistence_roundtrip():
    ctx = WorkflowContext.create(
        workflow_id="persist",
        vertical="AGRO",
        telegram_user={"id": 123, "name": "Client"},
        variables={"product": "wheat"},
    )
    ctx.request = {"request_number": "AGRO-00001"}
    payload = ctx.to_dict()
    restored = WorkflowContext.from_dict(payload)
    assert restored.execution_id == ctx.execution_id
    assert restored.variables["product"] == "wheat"
    assert restored.request["request_number"] == "AGRO-00001"


@pytest.mark.asyncio
async def test_backend_workflow_publishes_events():
    registry = WorkflowRegistry()
    definition = parse_workflow_document(
        {
            "workflow": {
                "id": "backend",
                "vertical": "CRM",
                "steps": [
                    {
                        "id": "audit",
                        "type": "service",
                        "service": "AuditService",
                        "method": "audit",
                    },
                    {"id": "done", "type": "complete"},
                ],
            }
        }
    )
    registry.register(definition)
    engine = WorkflowEngine(registry)
    engine._initialized = True

    published: list = []

    async def _capture(event, *, wait=False):
        published.append(event)
        return {"handlers": 0, "errors": []}

    with patch.object(engine, "_persist", new=AsyncMock()), patch.object(
        engine, "_log_step", new=AsyncMock()
    ), patch(
        "platform_workflows.workflow_steps.invoke_from_step_config",
        new=AsyncMock(return_value={"ok": True}),
    ), patch("platform_workflows.workflow_engine.publish", side_effect=_capture):
        result = await engine.run_backend_workflow(
            "CRM",
            telegram_user={"id": 1},
            request={"request_number": "CRM-0001"},
        )

    assert result is not None
    assert result.status == ExecutionStatus.COMPLETED
    assert any(isinstance(e, WorkflowStartedEvent) for e in published)
    assert any(isinstance(e, WorkflowCompletedEvent) for e in published)


@pytest.mark.asyncio
async def test_interactive_step_pauses_execution():
    registry = WorkflowRegistry()
    definition = parse_workflow_document(
        {
            "workflow": {
                "id": "interactive",
                "vertical": "AUTO",
                "steps": [
                    {"id": "phone", "type": "input", "variable": "phone"},
                    {"id": "done", "type": "complete"},
                ],
            }
        }
    )
    registry.register(definition)
    engine = WorkflowEngine(registry)
    engine._initialized = True

    with patch.object(engine, "_persist", new=AsyncMock()), patch(
        "platform_workflows.workflow_engine.publish", new=AsyncMock()
    ):
        ctx = await engine.start("interactive", telegram_user={"id": 99})

    assert ctx.status == ExecutionStatus.WAITING
    assert ctx.current_step == "phone"


@pytest.mark.asyncio
async def test_advance_resumes_workflow():
    registry = WorkflowRegistry()
    definition = parse_workflow_document(
        {
            "workflow": {
                "id": "resume",
                "vertical": "AUTO",
                "steps": [
                    {"id": "phone", "type": "input", "variable": "phone"},
                    {"id": "done", "type": "complete"},
                ],
            }
        }
    )
    registry.register(definition)
    engine = WorkflowEngine(registry)
    engine._initialized = True

    ctx = WorkflowContext.create(
        workflow_id="resume",
        vertical="AUTO",
        current_step="phone",
    )
    ctx.status = ExecutionStatus.WAITING
    engine._active[ctx.execution_id] = ctx

    with patch.object(engine, "_persist", new=AsyncMock()), patch.object(
        engine, "_log_step", new=AsyncMock()
    ), patch("platform_workflows.workflow_engine.publish", new=AsyncMock()):
        result = await engine.advance(ctx.execution_id, user_input="+380991234567")

    assert result.status == ExecutionStatus.COMPLETED
    assert result.variables.get("phone") == "+380991234567"


@pytest.mark.asyncio
async def test_dashboard_endpoint(monkeypatch, auth_headers):
    payload = {
        "registered_workflows": [],
        "active_executions": 0,
        "completed_today": 0,
        "failed_today": 0,
        "average_execution_time_ms": 0.0,
        "kpi": {
            "workflow_execution_time_ms": 0.0,
            "workflow_success_rate": 1.0,
            "workflow_failure_rate": 0.0,
            "step_execution_time_ms": 0.0,
            "active_workflows": 0,
        },
    }

    async def _owner(_tid):
        from platform_management.permissions import ManagementRole

        return ManagementRole.OWNER

    monkeypatch.setattr("platform_management.permissions.resolve_role", _owner)

    with patch(
        "workflow.workflow_engine.workflow_engine.get_statistics",
        new=AsyncMock(return_value=payload),
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        from aiohttp import web
        from platform_management.management_router import register_management_routes

        app = web.Application()
        register_management_routes(app)
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/management/v1/workflows", headers=auth_headers)
            assert resp.status == 200
            body = (await resp.json())["data"]
            assert "kpi" in body
            assert "registered_workflows" in body


@pytest.mark.asyncio
async def test_eventbus_kpi_invalidation():
    from workflow.workflow_kpi import workflow_kpi_service
    from services.kpi_service import kpi_service

    workflow_kpi_service.subscribe_to_event_bus()
    kpi_service._cache_set("test", {"value": 1})

    await workflow_kpi_service.handle_event(
        WorkflowCompletedEvent(
            execution_id=str(uuid.uuid4()),
            workflow_id="test",
            vertical="AUTO",
        )
    )
    assert kpi_service._cache_get("test") is None


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("RUN_WORKFLOW_PG_INTEGRATION") != "1",
    reason="PostgreSQL integration — set RUN_WORKFLOW_PG_INTEGRATION=1",
)
async def test_postgres_statistics_integration():
    from workflow import workflow_engine

    stats = await workflow_engine.get_statistics()
    assert "registered_workflows" in stats
    assert "kpi" in stats
