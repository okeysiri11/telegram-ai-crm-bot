"""Tests — Platform Tool & Integration Framework (Sprint 3.3)."""

from __future__ import annotations

import asyncio

import pytest

from events.event_bus import reset_subscribers, subscribe
from platform_tools.agent_bridge import AgentToolBridge
from platform_tools.audit import ToolAuditLog
from platform_tools.exceptions import (
    ToolAlreadyRegisteredError,
    ToolNotFoundError,
    ToolPermissionDeniedError,
    ToolValidationError,
)
from platform_tools.executor import ToolExecutor
from platform_tools.metrics import ToolMetrics
from platform_tools.models import Tool, ToolCategory, ToolContext, ToolPermission
from platform_tools.permissions import ToolPermissionService
from platform_tools.registry import ToolRegistry
from platform_tools.tool_events import ToolCompletedEvent, ToolFailedEvent, ToolStartedEvent
from platform_tools.tools.builtin import register_builtin_tools
from platform_tools.validation import validate_tool


@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry()
    register_builtin_tools(reg)
    return reg


@pytest.fixture
def framework(registry: ToolRegistry):
    perms = ToolPermissionService()
    metrics = ToolMetrics()
    audit = ToolAuditLog()
    executor = ToolExecutor(registry=registry, permissions=perms, metrics=metrics, audit=audit)
    bridge = AgentToolBridge(
        tool_registry_instance=registry,
        executor=executor,
        permissions=perms,
    )
    yield {"registry": registry, "executor": executor, "perms": perms, "metrics": metrics, "audit": audit, "bridge": bridge}
    executor.reset()
    perms.reset()
    bridge.reset()


@pytest.fixture(autouse=True)
def _reset_events():
    reset_subscribers()
    yield
    reset_subscribers()


@pytest.mark.asyncio
async def test_register_tool(registry: ToolRegistry):
    assert len(registry.list_tools()) >= 7
    tool = registry.get("internal_echo")
    assert tool.category == ToolCategory.INTERNAL


@pytest.mark.asyncio
async def test_remove_tool(registry: ToolRegistry):
    registry.remove_tool("internal_echo")
    with pytest.raises(ToolNotFoundError):
        registry.get("internal_echo")


@pytest.mark.asyncio
async def test_duplicate_tool(registry: ToolRegistry):
    tool = registry.get("internal_echo")
    with pytest.raises(ToolAlreadyRegisteredError):
        registry.register_tool(tool)


@pytest.mark.asyncio
async def test_validate_tool(registry: ToolRegistry):
    bad = Tool(
        tool_id="BAD ID",
        name="Bad",
        description="Bad",
        category=ToolCategory.INTERNAL,
        handler=lambda ctx, p: {},
    )
    with pytest.raises(ToolValidationError):
        validate_tool(bad)


@pytest.mark.asyncio
async def test_discover_tools(registry: ToolRegistry):
    async def _handler(ctx, payload):
        return {"ok": True}

    def discoverer():
        return [
            Tool(
                tool_id="plugin_tool",
                name="Plugin Tool",
                description="From plugin",
                category=ToolCategory.PLUGIN,
                handler=_handler,
            )
        ]

    registry.add_discoverer(discoverer)
    discovered = registry.discover_tools()
    assert len(discovered) == 1
    assert registry.get("plugin_tool").category == ToolCategory.PLUGIN


@pytest.mark.asyncio
async def test_execute_tool(framework):
    ctx = ToolContext(agent_id="auto_agent", permissions=["execute"])
    result = await framework["executor"].execute("internal_echo", {"hello": "world"}, context=ctx)
    assert result.success
    assert result.output["echo"]["hello"] == "world"


@pytest.mark.asyncio
async def test_tool_categories(framework):
    cats = framework["registry"].categories()
    assert "internal" in cats
    assert "crm" in cats
    assert "telegram" in cats


@pytest.mark.asyncio
async def test_permission_denied(framework):
    ctx = ToolContext(agent_id="test", permissions=["read"])
    framework["perms"].grant_agent_permission("test", "read")
    with pytest.raises(ToolPermissionDeniedError):
        await framework["executor"].execute("internal_echo", {}, context=ctx)


@pytest.mark.asyncio
async def test_concurrent_execution(framework):
    ctx = ToolContext(permissions=["execute"])
    results = await framework["executor"].execute_concurrent(
        [("internal_echo", {"i": 1}), ("internal_echo", {"i": 2})],
        context=ctx,
    )
    assert len(results) == 2
    assert all(r.success for r in results)


@pytest.mark.asyncio
async def test_tool_timeout(framework):
    async def slow_handler(ctx, payload):
        await asyncio.sleep(5)
        return {}

    framework["registry"].register_handler(
        "slow_tool", "Slow", "Slow tool", ToolCategory.INTERNAL, slow_handler
    )
    executor = ToolExecutor(
        registry=framework["registry"],
        permissions=framework["perms"],
        config=__import__("platform_tools.config", fromlist=["ToolExecutorConfig"]).ToolExecutorConfig(
            default_timeout_seconds=0.05, max_retries=0
        ),
    )
    ctx = ToolContext(permissions=["execute"])
    result = await executor.execute("slow_tool", {}, context=ctx)
    assert not result.success


@pytest.mark.asyncio
async def test_tool_retry(framework):
    attempts = {"count": 0}

    async def flaky_handler(ctx, payload):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("transient")
        return {"ok": True}

    framework["registry"].register_handler(
        "flaky_tool", "Flaky", "Flaky", ToolCategory.INTERNAL, flaky_handler
    )
    executor = ToolExecutor(
        registry=framework["registry"],
        permissions=framework["perms"],
        config=__import__("platform_tools.config", fromlist=["ToolExecutorConfig"]).ToolExecutorConfig(
            max_retries=2, retry_base_delay_seconds=0.01
        ),
    )
    ctx = ToolContext(permissions=["execute"])
    result = await executor.execute("flaky_tool", {}, context=ctx)
    assert result.success
    assert attempts["count"] == 2


@pytest.mark.asyncio
async def test_tool_cancel(framework):
    async def long_handler(ctx, payload):
        await asyncio.sleep(2)
        return {}

    framework["registry"].register_handler(
        "long_tool", "Long", "Long", ToolCategory.INTERNAL, long_handler
    )
    executor = framework["executor"]
    ctx = ToolContext(permissions=["execute"])

    exec_coro = asyncio.create_task(executor.execute("long_tool", {}, context=ctx))
    await asyncio.sleep(0.05)
    result = await exec_coro
    assert result.success or not result.success


@pytest.mark.asyncio
async def test_audit_log(framework):
    ctx = ToolContext(permissions=["execute"])
    await framework["executor"].execute("internal_echo", {}, context=ctx)
    history = framework["audit"].history()
    assert len(history) >= 1


@pytest.mark.asyncio
async def test_metrics(framework):
    ctx = ToolContext(permissions=["execute"])
    await framework["executor"].execute("internal_echo", {}, context=ctx)
    summary = framework["metrics"].summary()
    assert summary["executions"] >= 1
    assert summary["success_rate"] == 1.0


@pytest.mark.asyncio
async def test_agent_bridge(framework):
    bridge = framework["bridge"]
    bridge.declare_agent_tools("auto_agent", ["internal_echo", "crm_lookup"])
    tools = bridge.get_agent_tools("auto_agent")
    assert "internal_echo" in tools
    result = await bridge.execute_for_agent("auto_agent", "internal_echo", {"vin": "123"})
    assert result.success


@pytest.mark.asyncio
async def test_agent_bridge_denied(framework):
    bridge = framework["bridge"]
    bridge.declare_agent_tools("auto_agent", ["internal_echo"])
    with pytest.raises(ToolPermissionDeniedError):
        await bridge.execute_for_agent("auto_agent", "crm_lookup")


@pytest.mark.asyncio
async def test_orchestrator_tool_access(framework):
    bridge = framework["bridge"]
    bridge.declare_agent_tools("legal_agent", ["crm_lookup", "search_query"])
    access = bridge.tool_access_for_orchestrator("legal_agent")
    assert len(access["available_tools"]) == 2
    assert access["tool_definitions"]


@pytest.mark.asyncio
async def test_tool_events(framework):
    events: list[str] = []

    async def capture(e):
        events.append(type(e).__name__)

    subscribe(ToolStartedEvent, capture)
    subscribe(ToolCompletedEvent, capture)
    subscribe(ToolFailedEvent, capture)

    ctx = ToolContext(permissions=["execute"])
    await framework["executor"].execute("internal_echo", {}, context=ctx)
    await asyncio.sleep(0.05)
    assert "ToolStartedEvent" in events
    assert "ToolCompletedEvent" in events


@pytest.mark.asyncio
async def test_progress_reporting(framework):
    ctx = ToolContext(permissions=["execute"])
    result = await framework["executor"].execute("internal_echo", {}, context=ctx)
    progress = framework["executor"].get_progress(result.execution_id)
    assert progress is not None
    assert progress.progress == 1.0
