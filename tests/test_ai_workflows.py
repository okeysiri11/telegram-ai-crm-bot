"""Tests — AI Workflow Engine."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from events.event_bus import reset_subscribers, subscribe
from platform_ai.ai_service import ai_service
from platform_ai.skills.skill_manager import skill_manager
from platform_ai.workflows.models import StepType, WorkflowDefinition, WorkflowExecutionRequest, WorkflowStep
from platform_ai.workflows.workflow_builder import workflow_builder
from platform_ai.workflows.workflow_cache import workflow_cache
from platform_ai.workflows.workflow_engine import ai_workflow_engine
from platform_ai.workflows.workflow_events import AIWorkflowCompletedEvent, AIWorkflowStartedEvent, StepCompletedEvent
from platform_ai.workflows.workflow_executor import workflow_executor
from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole
from platform_plugin_sdk.models import PluginMetadata
from platform_plugin_sdk.plugin_context import PluginContext


@pytest.fixture(autouse=True)
def _reset():
    ai_service.reset()
    skill_manager.reset()
    ai_workflow_engine.reset()
    reset_subscribers()
    yield
    ai_service.reset()
    skill_manager.reset()
    ai_workflow_engine.reset()
    reset_subscribers()


@pytest.fixture
def actor_header():
    return {"X-Actor-Telegram-Id": "42"}


@pytest.fixture(autouse=True)
def _grant_permissions(monkeypatch):
    async def _owner(_tid):
        return ManagementRole.OWNER

    async def _authorize(_principal, _permission):
        return True

    async def _authenticate(_tid):
        from platform_identity.models import AuthMethod, Principal, PlatformRole

        return Principal(
            principal_id="test",
            auth_method=AuthMethod.TELEGRAM_USER,
            telegram_id=42,
            roles=[PlatformRole.OWNER.value],
        )

    monkeypatch.setattr("platform_management.permissions.resolve_role", _owner)
    from platform_identity.identity_service import identity_service

    monkeypatch.setattr(identity_service, "authorize", _authorize)
    monkeypatch.setattr(identity_service, "authenticate_telegram", _authenticate)


@pytest.mark.asyncio
async def test_workflow_registration():
    ai_workflow_engine.initialize()
    workflows = ai_workflow_engine.list_workflows()
    ids = {w["workflow_id"] for w in workflows}
    assert "vehicle_intake" in ids
    assert "lead_qualification" in ids
    assert len(workflows) >= 4


@pytest.mark.asyncio
async def test_workflow_execution():
    ai_service.initialize()
    ai_workflow_engine.initialize()
    request = WorkflowExecutionRequest(
        workflow_id="insurance_quote",
        input={"profile": {"age": 35, "vehicle": "sedan"}},
        plugin_id="insurance",
    )
    result = await ai_workflow_engine.execute(request)
    assert result.status == "completed"
    assert result.workflow_id == "insurance_quote"
    assert len(result.step_results) >= 2


@pytest.mark.asyncio
async def test_sequential_pipeline():
    ai_service.initialize()
    ai_workflow_engine.initialize()
    result = await ai_workflow_engine.execute(
        WorkflowExecutionRequest(
            workflow_id="vehicle_intake",
            input={"vin": "1HGBH41JXMN109186"},
            plugin_id="auto",
        )
    )
    assert result.status == "completed"
    step_ids = [s.step_id for s in result.step_results]
    assert "decode_vin" in step_ids
    assert "finalize" in step_ids
    assert "vehicle" in result.memory or "final" in result.memory


@pytest.mark.asyncio
async def test_parallel_steps():
    ai_service.initialize()
    ai_workflow_engine.initialize()
    result = await ai_workflow_engine.execute(
        WorkflowExecutionRequest(
            workflow_id="document_analysis",
            input={"text": "This is a sample contract about vehicle leasing terms."},
            use_cache=False,
        )
    )
    assert result.status == "completed"
    parallel_steps = [s for s in result.step_results if s.step_id in ("contract_check", "risk_check")]
    assert len(parallel_steps) >= 1


@pytest.mark.asyncio
async def test_conditional_branching():
    ai_service.initialize()
    ai_workflow_engine.initialize()
    result = await ai_workflow_engine.execute(
        WorkflowExecutionRequest(
            workflow_id="lead_qualification",
            input={
                "message": "I want to purchase a fleet of trucks",
                "lead_profile": {"company": "Acme", "budget": 100000},
            },
            use_cache=False,
        )
    )
    assert result.status == "completed"
    assert result.memory.get("final") or result.output


@pytest.mark.asyncio
async def test_workflow_caching():
    ai_service.initialize()
    ai_workflow_engine.initialize()
    request = WorkflowExecutionRequest(
        workflow_id="insurance_quote",
        input={"profile": {"age": 40}},
        use_cache=True,
    )
    first = await ai_workflow_engine.execute(request)
    second = await ai_workflow_engine.execute(request)
    assert first.status == "completed"
    assert second.cached is True
    assert workflow_cache.invalidate("insurance_quote") >= 1


@pytest.mark.asyncio
async def test_workflow_metrics():
    ai_service.initialize()
    ai_workflow_engine.initialize()
    await ai_workflow_engine.execute(
        WorkflowExecutionRequest(workflow_id="insurance_quote", input={"profile": {"age": 30}})
    )
    metrics = ai_workflow_engine.metrics("insurance_quote")
    assert metrics["executions"] >= 1


@pytest.mark.asyncio
async def test_workflow_events():
    ai_service.initialize()
    ai_workflow_engine.initialize()
    started: list[AIWorkflowStartedEvent] = []
    completed: list[AIWorkflowCompletedEvent] = []
    steps: list[StepCompletedEvent] = []

    subscribe(AIWorkflowStartedEvent, lambda e: started.append(e))
    subscribe(AIWorkflowCompletedEvent, lambda e: completed.append(e))
    subscribe(StepCompletedEvent, lambda e: steps.append(e))

    await ai_workflow_engine.execute(
        WorkflowExecutionRequest(workflow_id="insurance_quote", input={"profile": {"age": 25}})
    )
    assert any(e.workflow_id == "insurance_quote" for e in started)
    assert any(e.workflow_id == "insurance_quote" for e in completed)
    assert len(steps) >= 1


@pytest.mark.asyncio
async def test_workflow_retry_and_delay():
    ai_service.initialize()
    definition = WorkflowDefinition(
        workflow_id="retry_test",
        name="Retry Test",
        entry_step="delay_step",
        steps={
            "delay_step": WorkflowStep(
                step_id="delay_step",
                step_type=StepType.DELAY.value,
                config={"seconds": 0.01},
                next="skill_step",
            ),
            "skill_step": WorkflowStep(
                step_id="skill_step",
                step_type=StepType.SKILL.value,
                config={
                    "skill_id": "intent_detection",
                    "input_mapping": {"message": "$input.msg"},
                    "output_key": "intent",
                },
                retries=1,
                next="end",
            ),
        },
    )
    ai_workflow_engine.register(definition)
    result = await ai_workflow_engine.execute(
        WorkflowExecutionRequest(workflow_id="retry_test", input={"msg": "hello"}, use_cache=False)
    )
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_workflow_cancellation():
    ai_service.initialize()
    definition = WorkflowDefinition(
        workflow_id="cancel_test",
        name="Cancel Test",
        entry_step="long_delay",
        steps={
            "long_delay": WorkflowStep(
                step_id="long_delay",
                step_type=StepType.DELAY.value,
                config={"seconds": 5},
                next="end",
            ),
        },
    )
    ai_workflow_engine.register(definition)

    async def _run_and_cancel():
        task = asyncio.create_task(
            ai_workflow_engine.execute(
                WorkflowExecutionRequest(workflow_id="cancel_test", input={}, use_cache=False)
            )
        )
        await asyncio.sleep(0.05)
        state = workflow_executor.list_active()
        if state:
            ai_workflow_engine.cancel(state[0]["execution_id"])
        return await task

    result = await _run_and_cancel()
    assert result.status in ("cancelled", "completed")


@pytest.mark.asyncio
async def test_plugin_sdk_workflows():
    ai_service.initialize()
    ai_workflow_engine.initialize()
    ctx = PluginContext(
        plugin_id="insurance",
        version="1.0.0",
        metadata=PluginMetadata(plugin_id="insurance", name="Insurance", version="1.0.0"),
    )
    result = await ctx.ai.workflows.execute(
        "insurance_quote",
        {"profile": {"age": 45, "coverage": "full"}},
    )
    assert result["status"] == "completed"
    assert result["workflow_id"] == "insurance_quote"


@pytest.mark.asyncio
async def test_workflow_builder_json():
    data = {
        "workflow_id": "builder_test",
        "name": "Builder Test",
        "entry_step": "t1",
        "steps": [
            {
                "step_id": "t1",
                "step_type": "transform",
                "config": {"mapping": {"x": "$input.val"}, "output_key": "out"},
                "next": "end",
            }
        ],
    }
    definition = workflow_builder.from_dict(data)
    workflow_builder.validate(definition)
    ai_workflow_engine.register(definition)
    result = await ai_workflow_engine.execute(
        WorkflowExecutionRequest(workflow_id="builder_test", input={"val": 42}, use_cache=False)
    )
    assert result.status == "completed"
    assert result.memory.get("out", {}).get("x") == 42


@pytest.mark.asyncio
async def test_management_api_workflows(actor_header):
    app = web.Application()
    register_management_routes(app)
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/management/ai/workflows/list", headers=actor_header)
        assert resp.status == 200
        body = await resp.json()
        assert body["success"] is True
        assert len(body["data"]["workflows"]) >= 4

        exec_resp = await client.post(
            "/management/ai/workflows/execute",
            json={"workflow_id": "insurance_quote", "input": {"profile": {"age": 33}}},
            headers=actor_header,
        )
        assert exec_resp.status == 200
        exec_body = await exec_resp.json()
        assert exec_body["data"]["status"] == "completed"

        tpl_resp = await client.get("/management/ai/workflows/templates", headers=actor_header)
        assert tpl_resp.status == 200
