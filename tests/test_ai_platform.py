"""Tests — Platform AI Platform."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from events.event_bus import reset_subscribers, subscribe
from platform_ai.ai_events import AIFallbackUsedEvent, AIRequestCompletedEvent, AIRequestStartedEvent
from platform_ai.ai_service import ai_service
from platform_ai.cache import ai_cache
from platform_ai.cost_tracker import cost_tracker
from platform_ai.models import AIRequest, TaskType
from platform_ai.prompt_service import prompt_service
from platform_ai.provider_base import MockAIProvider
from platform_ai.provider_manager import provider_manager
from platform_ai.provider_registry import provider_registry
from platform_ai.provider_router import provider_router
from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole


@pytest.fixture(autouse=True)
def _reset_ai():
    ai_service.reset()
    reset_subscribers()
    yield
    ai_service.reset()
    reset_subscribers()


@pytest.fixture
def actor_header():
    return {"X-Actor-Telegram-Id": "42"}


@pytest.fixture(autouse=True)
def _grant_ai_permissions(monkeypatch):
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
async def test_auto_routing():
    ai_service.initialize()
    request = AIRequest(prompt="Hello", task_type=TaskType.CHAT)
    decision = provider_router.route(request)
    assert decision.provider_id in provider_manager.fallback_chain
    assert decision.model_id


@pytest.mark.asyncio
async def test_explicit_provider_routing():
    ai_service.initialize()
    request = AIRequest(prompt="Hi", provider="anthropic", model="claude-3-haiku")
    decision = provider_router.route(request)
    assert decision.provider_id == "anthropic"
    assert decision.model_id == "claude-3-haiku"


@pytest.mark.asyncio
async def test_complete_request():
    events: list[str] = []

    async def capture_started(event: AIRequestStartedEvent) -> None:
        events.append("started")

    async def capture_completed(event: AIRequestCompletedEvent) -> None:
        events.append("completed")

    subscribe(AIRequestStartedEvent, capture_started)
    subscribe(AIRequestCompletedEvent, capture_completed)

    response = await ai_service.complete(AIRequest(prompt="Test prompt", task_type=TaskType.CHAT))
    assert response.content
    assert response.provider_id
    assert response.tokens_in > 0
    assert response.cost_usd >= 0
    await asyncio.sleep(0.02)
    assert "started" in events
    assert "completed" in events


@pytest.mark.asyncio
async def test_prompt_cache():
    await ai_service.complete(AIRequest(prompt="Cache me", task_type=TaskType.CHAT, use_cache=True))
    r2 = await ai_service.complete(AIRequest(prompt="Cache me", task_type=TaskType.CHAT, use_cache=True))
    assert r2.cached
    assert ai_cache.stats()["hits"] >= 1


@pytest.mark.asyncio
async def test_cache_invalidation():
    await ai_service.complete(AIRequest(prompt="X", task_type=TaskType.CHAT))
    assert ai_cache.stats()["entries"] >= 1
    removed = ai_cache.invalidate()
    assert removed >= 1


@pytest.mark.asyncio
async def test_provider_fallback():
    ai_service.initialize()
    failing = MockAIProvider("openai", "OpenAI", fail=True)
    provider_registry.register(failing)
    provider_manager.enable("openai")

    response = await ai_service.complete(
        AIRequest(prompt="Fallback test", provider="openai", model="gpt-4o-mini", use_cache=False)
    )
    assert response.content


def test_prompt_rendering():
    ai_service.initialize()
    rendered = prompt_service.render(
        "request.summary",
        {"request_number": "AUTO-001", "description": "Buy car", "client_name": "John"},
    )
    assert "AUTO-001" in rendered
    assert "Buy car" in rendered


def test_prompt_validation():
    ai_service.initialize()
    with pytest.raises(Exception):
        prompt_service.render("request.summary", {"request_number": "X"})


@pytest.mark.asyncio
async def test_cost_tracking():
    await ai_service.complete(AIRequest(prompt="Cost test", task_type=TaskType.CHAT, use_cache=False))
    summary = cost_tracker.summary()
    assert summary["request_count"] >= 1
    assert summary["total_usd"] >= 0
    assert summary["tokens_in"] > 0


def test_task_based_routing():
    ai_service.initialize()
    code_decision = provider_router.route(AIRequest(prompt="code", task_type=TaskType.CODE))
    chat_decision = provider_router.route(AIRequest(prompt="chat", task_type=TaskType.CHAT))
    assert code_decision.provider_id
    assert chat_decision.provider_id


@pytest.mark.asyncio
async def test_management_api_ai(actor_header):
    app = web.Application()
    register_management_routes(app)

    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/management/ai/providers", headers=actor_header)
        body = await resp.json()
        assert body["success"] is True
        assert len(body["data"]["providers"]) >= 6

        resp = await client.get("/management/ai/models", headers=actor_header)
        models = await resp.json()
        assert len(models["data"]["models"]) >= 9

        resp = await client.post(
            "/management/ai/complete",
            json={"prompt": "API test", "task_type": "chat"},
            headers=actor_header,
        )
        result = await resp.json()
        assert result["success"] is True
        assert result["data"]["content"]
