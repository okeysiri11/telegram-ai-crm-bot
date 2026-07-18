"""Tests — AI Skills Framework."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from events.event_bus import reset_subscribers, subscribe
from platform_ai.ai_service import ai_service
from platform_ai.skills.exceptions import SkillDisabledError, SkillValidationError
from platform_ai.skills.models import SkillExecutionRequest, SkillExecutionResult
from platform_ai.skills.skill_base import AISkill
from platform_ai.skills.skill_cache import skill_cache
from platform_ai.skills.skill_context import SkillContext
from platform_ai.skills.skill_events import SkillExecutedEvent, SkillLoadedEvent
from platform_ai.skills.skill_manager import skill_manager
from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole
from platform_plugin_sdk.models import PluginMetadata
from platform_plugin_sdk.plugin_context import PluginContext


@pytest.fixture(autouse=True)
def _reset_skills():
    ai_service.reset()
    skill_manager.reset()
    reset_subscribers()
    yield
    ai_service.reset()
    skill_manager.reset()
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
async def test_skill_registration():
    skill_manager.initialize()
    skills = skill_manager.list_skills()
    ids = {s["skill_id"] for s in skills}
    assert "lead_scoring" in ids
    assert "vin_decoder" in ids
    assert len(skills) >= 10


@pytest.mark.asyncio
async def test_skill_load_and_validate():
    skill_manager.initialize()
    record = await skill_manager.load("document_summary")
    assert record.state.value == "loaded"
    with pytest.raises(SkillValidationError):
        skill_manager.validate("document_summary", {})


@pytest.mark.asyncio
async def test_skill_execution():
    ai_service.initialize()
    skill_manager.initialize()
    request = SkillExecutionRequest(
        skill_id="intent_detection",
        input={"message": "I want to buy a car"},
        plugin_id="auto",
    )
    result = await skill_manager.execute(request)
    assert result.success
    assert result.skill_id == "intent_detection"
    assert result.tokens_out >= 0


@pytest.mark.asyncio
async def test_skill_caching():
    ai_service.initialize()
    skill_manager.initialize()
    request = SkillExecutionRequest(
        skill_id="document_summary",
        input={"text": "Long document about vehicles."},
        plugin_id="auto",
        use_cache=True,
    )
    first = await skill_manager.execute(request)
    second = await skill_manager.execute(request)
    assert first.success and second.success
    assert second.cached is True
    assert skill_cache.invalidate("document_summary") >= 1


@pytest.mark.asyncio
async def test_skill_metrics():
    ai_service.initialize()
    skill_manager.initialize()
    await skill_manager.execute(
        SkillExecutionRequest(skill_id="document_summary", input={"text": "Sample text for metrics."})
    )
    metrics = skill_manager.metrics("document_summary")
    assert metrics["executions"] >= 1
    assert metrics["success_rate"] >= 0


@pytest.mark.asyncio
async def test_skill_disable():
    ai_service.initialize()
    skill_manager.initialize()
    await skill_manager.disable("lead_scoring")
    with pytest.raises(SkillDisabledError):
        await skill_manager.execute(
            SkillExecutionRequest(skill_id="lead_scoring", input={"lead_profile": {"name": "Test"}})
        )


@pytest.mark.asyncio
async def test_skill_events():
    ai_service.initialize()
    skill_manager.initialize()
    loaded: list[SkillLoadedEvent] = []
    executed: list[SkillExecutedEvent] = []

    subscribe(SkillLoadedEvent, lambda e: loaded.append(e))
    subscribe(SkillExecutedEvent, lambda e: executed.append(e))

    await skill_manager.load("price_estimation")
    await skill_manager.execute(
        SkillExecutionRequest(
            skill_id="price_estimation",
            input={"item_description": "Used sedan 2018"},
        )
    )
    assert any(e.skill_id == "price_estimation" for e in loaded)
    assert any(e.skill_id == "price_estimation" for e in executed)


@pytest.mark.asyncio
async def test_plugin_sdk_skills_execute():
    ai_service.initialize()
    skill_manager.initialize()
    ctx = PluginContext(
        plugin_id="auto",
        version="1.0.0",
        metadata=PluginMetadata(plugin_id="auto", name="Auto", version="1.0.0"),
    )
    result = await ctx.ai.skills.execute(
        "vehicle_description",
        {"vehicle_specs": {"make": "Toyota", "model": "Camry", "year": 2020}},
    )
    assert result["success"] is True
    assert result["skill_id"] == "vehicle_description"


@pytest.mark.asyncio
async def test_management_api_skills(actor_header):
    app = web.Application()
    register_management_routes(app)
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/management/ai/skills/list", headers=actor_header)
        assert resp.status == 200
        body = await resp.json()
        assert body["success"] is True
        assert len(body["data"]["skills"]) >= 10

        exec_resp = await client.post(
            "/management/ai/skills/execute",
            json={"skill_id": "risk_assessment", "input": {"scenario": "Fleet expansion"}},
            headers=actor_header,
        )
        assert exec_resp.status == 200
        exec_body = await exec_resp.json()
        assert exec_body["data"]["success"] is True


@pytest.mark.asyncio
async def test_custom_skill_registration():
    class EchoSkill(AISkill):
        skill_id = "echo_test"
        name = "Echo Test"
        tags = ["test"]
        _uses_ai = False

        async def execute(self, ctx: SkillContext) -> SkillExecutionResult:
            return SkillExecutionResult(
                skill_id=self.skill_id,
                execution_id="test",
                success=True,
                output={"echo": ctx.input.get("value", "")},
            )

    skill_manager.register(EchoSkill)
    record = await skill_manager.load("echo_test")
    assert record.skill_id == "echo_test"
    result = await skill_manager.execute(SkillExecutionRequest(skill_id="echo_test", input={"value": "hello"}))
    assert result.output["echo"] == "hello"
