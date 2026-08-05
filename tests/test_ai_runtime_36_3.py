"""Tests — AI Runtime (Sprint 36.3)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_ai.router import register_ai_runtime_routes
from platform_ai.service import ai_runtime_service as ars
from platform_management.permissions import ManagementRole


@pytest.fixture
def runtime():
    ars.reset()
    ars.ensure_ready()
    yield ars
    ars.reset()


@pytest.mark.asyncio
async def test_multi_provider_support(runtime):
    providers = await runtime.providers()
    ids = {p["provider_id"] for p in providers}
    for required in ("openai", "anthropic", "google", "ollama", "openrouter", "azure_openai"):
        assert required in ids
    assert len(providers) >= 6


@pytest.mark.asyncio
async def test_automatic_model_routing(runtime):
    decision = runtime.preview_route({"prompt": "hello", "task_type": "chat"})
    assert decision["provider_id"]
    assert decision["model_id"]
    assert "fallback_chain" in decision
    assert "openai" in decision["fallback_chain"]


@pytest.mark.asyncio
async def test_prompt_runtime(runtime):
    created = runtime.create_prompt(
        {
            "template_id": "sprint.hello",
            "name": "Hello",
            "system_prompt": "System for {{brand}}",
            "body": "Say hello to {{name}}",
        }
    )
    assert created["template_id"] == "sprint.hello"
    valid = runtime.validate_prompt("sprint.hello", {"variables": {"brand": "ADOS", "name": "Owner"}})
    assert valid["valid"] is True
    rendered = runtime.render_prompt(
        "sprint.hello",
        {"variables": {"brand": "ADOS", "name": "Owner"}},
    )
    assert "ADOS" in rendered["rendered"]
    assert "Owner" in rendered["rendered"]
    v2 = runtime.version_prompt(
        "sprint.hello",
        {"body": "Hi {{name}} from {{brand}}", "system_prompt": "v2", "changelog": "simplify"},
    )
    assert v2["version"] == 2
    versions = runtime.prompt_versions("sprint.hello")
    assert any(v["version"] == 2 for v in versions)
    # cache hit
    again = runtime.render_prompt(
        "sprint.hello",
        {"variables": {"brand": "ADOS", "name": "Owner"}, "version": 1},
    )
    # first render after version may miss; second should hit
    third = runtime.render_prompt(
        "sprint.hello",
        {"variables": {"brand": "ADOS", "name": "Owner"}, "version": 1},
    )
    assert third["cached"] is True or again["cached"] is True or third["cache_hits"] >= 1


@pytest.mark.asyncio
async def test_tool_runtime_and_function_calling(runtime):
    tools = runtime.list_tools()
    assert any(t["name"] == "echo" for t in tools)
    schemas = runtime.function_schemas()
    assert schemas and schemas[0]["type"] == "function"
    assert any(t.get("mcp_compatible") for t in tools)
    rec = await runtime.execute_tool("tool_add", {"arguments": {"a": 2, "b": 3}})
    assert rec["success"] is True
    assert rec["result"]["sum"] == 5.0
    denied = runtime.register_tool(
        {
            "tool_id": "tool_denied",
            "name": "denied",
            "permission": "deny",
        }
    )
    assert denied["permission"] == "deny"
    bad = await runtime.execute_tool("tool_denied", {"arguments": {}})
    assert bad["success"] is False
    assert runtime.tool_executions()


@pytest.mark.asyncio
async def test_complete_with_session_and_audit(runtime):
    session = runtime.create_session({"user_id": "u1"})
    result = await runtime.complete(
        {
            "session_id": session["session_id"],
            "prompt": "ping enterprise",
            "use_cache": False,
            "tool_calls": [{"tool_id": "tool_echo", "arguments": {"text": "hi"}}],
        }
    )
    assert result["content"]
    assert result["provider_id"]
    assert result["session_id"] == session["session_id"]
    assert result["tool_calls"] and result["tool_calls"][0]["success"]
    logs = runtime.logs()
    assert any(l["message"] == "request_completed" for l in logs)
    closed = runtime.close_session(session["session_id"])
    assert closed["status"] == "completed"


@pytest.mark.asyncio
async def test_provider_failover(runtime):
    from platform_ai.provider_manager import provider_manager
    from platform_ai.provider_registry import provider_registry

    runtime.ensure_ready()
    primary = provider_manager.default_provider
    provider = provider_registry.get(primary)

    original = provider.complete

    async def boom(request, *, model_id: str):
        raise RuntimeError("forced failure")

    provider.complete = boom  # type: ignore[method-assign]
    try:
        result = await runtime.complete({"prompt": "failover please", "use_cache": False, "provider": primary})
        assert result["content"]
        assert result.get("fallback_used") is True or result["provider_id"] != primary
    finally:
        provider.complete = original  # type: ignore[method-assign]


@pytest.mark.asyncio
async def test_monitoring(runtime):
    await runtime.complete({"prompt": "monitor", "use_cache": False, "create_session": True})
    mon = runtime.monitoring()
    assert mon["requests"] >= 1
    assert mon["sessions_total"] >= 1
    assert mon["tools"] >= 1
    status = runtime.status()
    assert status["canonical"] == "platform_ai"
    assert status["mcp_compatible"] is True
    assert status["function_calling"] is True


@pytest.mark.asyncio
async def test_rest_api(runtime, auth_headers, monkeypatch):
    async def _admin(_tid):
        return ManagementRole.ADMINISTRATOR

    monkeypatch.setattr("platform_management.permissions.resolve_role", _admin)
    app = web.Application()
    register_ai_runtime_routes(app)

    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            res = await client.get("/api/ai-runtime/providers", headers=auth_headers)
            assert res.status == 200
            body = await res.json()
            assert body["data"]["count"] >= 6

            res = await client.post(
                "/api/llm/complete",
                headers=auth_headers,
                json={"prompt": "via llm api", "use_cache": False},
            )
            assert res.status == 200
            assert (await res.json())["data"]["content"]

            res = await client.get("/api/prompts", headers=auth_headers)
            assert res.status == 200

            res = await client.get("/api/ai-runtime/tools", headers=auth_headers)
            assert res.status == 200

            res = await client.get("/api/ai-runtime/monitoring", headers=auth_headers)
            assert res.status == 200

            res = await client.get("/management/v1/ai-runtime/status", headers=auth_headers)
            assert res.status == 200

    ars.reset()


def test_ui_present():
    from pathlib import Path

    page = Path(__file__).resolve().parents[1] / "src/web/src/ai-runtime-console/AIRuntimeConsolePage.tsx"
    text = page.read_text(encoding="utf-8")
    for label in (
        "Providers",
        "Models",
        "Runtime",
        "Sessions",
        "Prompt Studio",
        "Tool Registry",
        "Execution Logs",
        "Monitoring",
    ):
        assert label in text


def test_orm_tables():
    from database.models.ai_runtime import (
        AIModelRow,
        AIProviderRow,
        AIRuntimeLogRow,
        AIRuntimeSessionRow,
        PromptTemplateRow,
        PromptVersionRow,
        ToolExecutionRow,
        ToolRegistryRow,
    )

    assert AIProviderRow.__tablename__ == "ai_providers"
    assert AIModelRow.__tablename__ == "ai_models"
    assert AIRuntimeSessionRow.__tablename__ == "ai_runtime_sessions"
    assert PromptTemplateRow.__tablename__ == "prompt_templates"
    assert PromptVersionRow.__tablename__ == "prompt_versions"
    assert ToolRegistryRow.__tablename__ == "tool_registry"
    assert ToolExecutionRow.__tablename__ == "tool_executions"
    assert AIRuntimeLogRow.__tablename__ == "ai_runtime_logs"


def test_migration_present():
    from pathlib import Path

    mig = Path(__file__).resolve().parents[1] / "migrations/versions/l5f678901234_ai_runtime_v1.py"
    text = mig.read_text(encoding="utf-8")
    for table in (
        "ai_providers",
        "ai_models",
        "ai_runtime_sessions",
        "prompt_templates",
        "prompt_versions",
        "tool_registry",
        "tool_executions",
        "ai_runtime_logs",
    ):
        assert table in text


def test_exports():
    from platform_ai import ai_runtime_service, ai_service
    from platform_ai.runtime_engine import AIRuntimeEngine, ai_runtime_engine
    from platform_ai.tool_runtime import ToolRuntime, tool_runtime

    assert ai_service and ai_runtime_service
    assert AIRuntimeEngine and ai_runtime_engine
    assert ToolRuntime and tool_runtime
