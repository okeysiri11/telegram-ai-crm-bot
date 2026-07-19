"""Tests — Platform Multi-Agent Orchestrator (Sprint 2.3)."""

from __future__ import annotations

import asyncio

import pytest

from platform_orchestrator.agent_registry import AgentRegistry
from platform_orchestrator.agents.builtin import (
    AgroAgent,
    AutoAgent,
    BUILTIN_AGENTS,
    ERPAgent,
    LegalAgent,
    PortAgent,
    register_builtin_agents,
)
from platform_orchestrator.base_agent import BaseAgent
from platform_orchestrator.capability_routing import CapabilityRouter
from platform_orchestrator.config import OrchestratorConfig
from platform_orchestrator.exceptions import (
    AgentAlreadyRegisteredError,
    AgentNotFoundError,
    CapabilityNotRoutableError,
    TaskValidationError,
)
from platform_orchestrator.message_bus import AgentMessageBus
from platform_orchestrator.metrics import OrchestratorMetrics
from platform_orchestrator.models import (
    AgentContext,
    AgentMessage,
    AgentStatus,
    MessageType,
    TaskRequest,
    TaskResult,
    TaskStatus,
)
from platform_orchestrator.orchestrator import PlatformOrchestrator


@pytest.fixture
def registry() -> AgentRegistry:
    reg = AgentRegistry()
    register_builtin_agents(reg)
    return reg


@pytest.fixture
def orchestrator(registry: AgentRegistry) -> PlatformOrchestrator:
    bus = AgentMessageBus()
    metrics = OrchestratorMetrics()
    router = CapabilityRouter(registry)
    orch = PlatformOrchestrator(
        registry=registry,
        router=router,
        message_bus=bus,
        metrics=metrics,
        config=OrchestratorConfig(
            default_timeout_seconds=2.0,
            max_retries=2,
            retry_base_delay_seconds=0.01,
            retry_max_delay_seconds=0.05,
        ),
    )
    yield orch
    orch.reset()


@pytest.mark.asyncio
async def test_registry_register_and_list(registry: AgentRegistry):
    assert len(registry.list()) == len(BUILTIN_AGENTS)
    meta = registry.metadata("auto_agent")
    assert meta.name == "Auto Agent"
    assert "buy_car" in meta.capabilities


@pytest.mark.asyncio
async def test_registry_unregister(registry: AgentRegistry):
    registry.unregister("auto_agent")
    with pytest.raises(AgentNotFoundError):
        registry.get("auto_agent")


@pytest.mark.asyncio
async def test_registry_duplicate_register(registry: AgentRegistry):
    with pytest.raises(AgentAlreadyRegisteredError):
        registry.register(AutoAgent)


@pytest.mark.asyncio
async def test_registry_capabilities(registry: AgentRegistry):
    caps = registry.capabilities()
    assert caps["buy_car"] == ["auto_agent"]
    assert caps["legal_contract"] == ["legal_agent"]
    assert caps["market_analysis"] == ["erp_agent"]
    assert caps["shipment_tracking"] == ["port_agent"]


@pytest.mark.asyncio
async def test_registry_health(registry: AgentRegistry):
    health = await registry.health()
    assert "auto_agent" in health
    assert health["auto_agent"].healthy is True


@pytest.mark.asyncio
async def test_capability_router_buy_car(registry: AgentRegistry):
    router = CapabilityRouter(registry)
    decision = router.route("buy_car")
    assert decision.agent_id == "auto_agent"
    assert decision.agent_name == "Auto Agent"


@pytest.mark.asyncio
async def test_capability_router_legal_contract(registry: AgentRegistry):
    router = CapabilityRouter(registry)
    decision = router.route("legal_contract")
    assert decision.agent_id == "legal_agent"


@pytest.mark.asyncio
async def test_capability_router_market_analysis(registry: AgentRegistry):
    router = CapabilityRouter(registry)
    decision = router.route("market_analysis")
    assert decision.agent_id == "erp_agent"


@pytest.mark.asyncio
async def test_capability_router_shipment_tracking(registry: AgentRegistry):
    router = CapabilityRouter(registry)
    decision = router.route("shipment_tracking")
    assert decision.agent_id == "port_agent"


@pytest.mark.asyncio
async def test_capability_router_unknown(registry: AgentRegistry):
    router = CapabilityRouter(registry)
    with pytest.raises(CapabilityNotRoutableError):
        router.route("nonexistent_capability")


@pytest.mark.asyncio
async def test_capability_router_fallback(registry: AgentRegistry):
    router = CapabilityRouter(registry)
    decision = router.route_with_fallback("unknown_cap", "buy_car")
    assert decision.agent_id == "auto_agent"


@pytest.mark.asyncio
async def test_orchestrator_execute_async(orchestrator: PlatformOrchestrator):
    ctx = AgentContext(
        user_context={"user_id": "u1"},
        memory_context={"facts": ["prefers diesel"]},
        session_context={"session_id": "s1"},
        platform_context={"tenant": "bidex"},
        permissions=["agent.execute"],
    )
    task = TaskRequest(capability="buy_car", payload={"model": "SUV"}, context=ctx)
    result = await orchestrator.execute_async(task)
    assert result.success
    assert result.agent_id == "auto_agent"
    assert result.output["acknowledged"] is True
    assert result.preserved_context["user_context"]["user_id"] == "u1"


def test_orchestrator_sync_execute():
    registry = AgentRegistry()
    register_builtin_agents(registry)
    orch = PlatformOrchestrator(registry=registry, router=CapabilityRouter(registry))
    task = TaskRequest(capability="legal_contract", payload={"doc_id": "d1"})
    result = orch.execute(task)
    assert result.success
    assert result.agent_id == "legal_agent"
    orch.reset()


@pytest.mark.asyncio
async def test_orchestrator_routing_all_verticals(orchestrator: PlatformOrchestrator):
    routes = {
        "buy_car": "auto_agent",
        "grain_trade": "agro_agent",
        "legal_contract": "legal_agent",
        "market_analysis": "erp_agent",
        "shipment_tracking": "port_agent",
        "create_listing": "marketplace_agent",
        "cafe_order": "cafe_agent",
        "book_appointment": "beauty_agent",
    }
    for capability, expected_agent in routes.items():
        result = await orchestrator.execute_async(TaskRequest(capability=capability))
        assert result.agent_id == expected_agent, f"{capability} -> {result.agent_id}"


@pytest.mark.asyncio
async def test_orchestrator_unroutable(orchestrator: PlatformOrchestrator):
    result = await orchestrator.execute_async(TaskRequest(capability="unknown_xyz"))
    assert result.status == TaskStatus.FAILED
    assert result.error_code == "capability_not_routable"


@pytest.mark.asyncio
async def test_orchestrator_timeout(orchestrator: PlatformOrchestrator):
    class SlowAgent(BaseAgent):
        agent_id = "slow_agent"
        name = "Slow"
        description = "Slow agent"
        capabilities = ["slow_task"]
        priority = 200

        async def execute(self, task: TaskRequest) -> TaskResult:
            await asyncio.sleep(5)
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                capability=task.capability,
                status=TaskStatus.COMPLETED,
            )

    orchestrator.registry.register(SlowAgent)
    task = TaskRequest(capability="slow_task", timeout_seconds=0.05, max_retries=0)
    result = await orchestrator.execute_async(task)
    assert result.status == TaskStatus.TIMEOUT
    assert result.error_code == "task_timeout"


@pytest.mark.asyncio
async def test_orchestrator_retry_recovery(orchestrator: PlatformOrchestrator):
    attempts = {"count": 0}

    class FlakyAgent(BaseAgent):
        agent_id = "flaky_agent"
        name = "Flaky"
        description = "Fails then succeeds"
        capabilities = ["flaky_task"]
        priority = 200

        async def execute(self, task: TaskRequest) -> TaskResult:
            attempts["count"] += 1
            if attempts["count"] < 2:
                raise RuntimeError("transient failure")
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                capability=task.capability,
                status=TaskStatus.COMPLETED,
                output={"recovered": True},
            )

    orchestrator.registry.register(FlakyAgent)
    result = await orchestrator.execute_async(TaskRequest(capability="flaky_task"))
    assert result.success
    assert attempts["count"] == 2
    assert result.retries == 1


@pytest.mark.asyncio
async def test_orchestrator_retry_exhausted(orchestrator: PlatformOrchestrator):
    class AlwaysFailAgent(BaseAgent):
        agent_id = "fail_agent"
        name = "Fail"
        description = "Always fails"
        capabilities = ["fail_task"]
        priority = 200

        async def execute(self, task: TaskRequest) -> TaskResult:
            raise RuntimeError("permanent failure")

    orchestrator.registry.register(AlwaysFailAgent)
    task = TaskRequest(capability="fail_task", max_retries=1)
    result = await orchestrator.execute_async(task)
    assert result.status == TaskStatus.FAILED
    assert result.error_code == "task_retry_exhausted"
    assert result.preserved_context  # context preserved


@pytest.mark.asyncio
async def test_orchestrator_validation_error(orchestrator: PlatformOrchestrator):
    class StrictAgent(BaseAgent):
        agent_id = "strict_agent"
        name = "Strict"
        description = "Validates input"
        capabilities = ["strict_task"]
        priority = 200

        def validate(self, task: TaskRequest) -> None:
            if "required_field" not in task.payload:
                raise TaskValidationError("missing required_field")

        async def execute(self, task: TaskRequest) -> TaskResult:
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                capability=task.capability,
                status=TaskStatus.COMPLETED,
            )

    orchestrator.registry.register(StrictAgent)
    result = await orchestrator.execute_async(TaskRequest(capability="strict_task", payload={}))
    assert result.status == TaskStatus.FAILED
    assert result.error_code == "task_validation_error"


@pytest.mark.asyncio
async def test_orchestrator_cancel(orchestrator: PlatformOrchestrator):
    class LongAgent(BaseAgent):
        agent_id = "long_agent"
        name = "Long"
        description = "Long running"
        capabilities = ["long_task"]
        priority = 200

        async def execute(self, task: TaskRequest) -> TaskResult:
            await asyncio.sleep(2)
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                capability=task.capability,
                status=TaskStatus.COMPLETED,
            )

    orchestrator.registry.register(LongAgent)
    task = TaskRequest(task_id="cancel-me", capability="long_task")
    exec_coro = asyncio.create_task(orchestrator.execute_async(task))
    await asyncio.sleep(0.05)
    orchestrator.cancel("cancel-me")
    result = await exec_coro
    assert result.status == TaskStatus.CANCELLED


@pytest.mark.asyncio
async def test_orchestrator_queue(orchestrator: PlatformOrchestrator):
    t1 = TaskRequest(capability="buy_car")
    t2 = TaskRequest(capability="legal_contract")
    await orchestrator.enqueue(t1)
    await orchestrator.enqueue(t2)
    results = await orchestrator.process_queue()
    assert len(results) == 2
    assert all(r.success for r in results)


@pytest.mark.asyncio
async def test_message_bus_request_response(orchestrator: PlatformOrchestrator):
    await orchestrator.initialize()
    response = await orchestrator.request_agent(
        "orchestrator",
        "auto_agent",
        {"capability": "buy_car", "payload": {"q": "test"}},
        timeout_seconds=2.0,
    )
    assert response.message_type == MessageType.RESPONSE
    assert response.payload["status"] == "completed"


@pytest.mark.asyncio
async def test_message_bus_notification(orchestrator: PlatformOrchestrator):
    received: list[AgentMessage] = []

    async def handler(msg: AgentMessage) -> None:
        received.append(msg)

    orchestrator.message_bus.subscribe(MessageType.NOTIFICATION, handler)
    await orchestrator.message_bus.notify("auto_agent", {"hello": "world"})
    assert len(received) == 1
    assert received[0].payload["hello"] == "world"


@pytest.mark.asyncio
async def test_metrics(orchestrator: PlatformOrchestrator):
    await orchestrator.execute_async(TaskRequest(capability="buy_car"))
    await orchestrator.execute_async(TaskRequest(capability="unknown"))
    summary = orchestrator.metrics.summary()
    assert summary["executions"] == 2
    assert summary["failures"] == 1
    assert summary["routing_decisions"] >= 1
    assert "auto_agent" in orchestrator.metrics.for_agent("auto_agent")["agent_id"]


@pytest.mark.asyncio
async def test_inactive_agent_excluded_from_routing(registry: AgentRegistry):
    registry.set_status("auto_agent", AgentStatus.INACTIVE)
    router = CapabilityRouter(registry)
    with pytest.raises(CapabilityNotRoutableError):
        router.route("buy_car")


@pytest.mark.asyncio
async def test_agent_context_no_global_state(orchestrator: PlatformOrchestrator):
    ctx = AgentContext(user_context={"isolated": True})
    result = await orchestrator.execute_async(
        TaskRequest(capability="grain_trade", context=ctx, payload={"crop": "wheat"})
    )
    assert result.agent_id == "agro_agent"
    assert result.preserved_context["user_context"]["isolated"] is True


@pytest.mark.asyncio
async def test_builtin_agents_metadata():
    auto = AutoAgent.metadata()
    agro = AgroAgent.metadata()
    legal = LegalAgent.metadata()
    erp = ERPAgent.metadata()
    port = PortAgent.metadata()
    assert auto.id == "auto_agent"
    assert agro.id == "agro_agent"
    assert legal.id == "legal_agent"
    assert erp.id == "erp_agent"
    assert port.id == "port_agent"
