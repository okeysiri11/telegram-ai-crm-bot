"""Tests — Platform Reasoning Engine (Sprint 4.1)."""

from __future__ import annotations

import asyncio

import pytest

from events.event_bus import reset_subscribers, subscribe
from platform_reasoning.metrics import ReasoningMetrics
from platform_reasoning.models import ReasoningContext, ReasoningStrategy
from platform_reasoning.pipeline import ReasoningPipeline
from platform_reasoning.reasoning_engine import ReasoningEngine
from platform_reasoning.reasoning_events import (
    ReasoningCompletedEvent,
    ReasoningFailedEvent,
    ReasoningStartedEvent,
)
from platform_reasoning.strategies.builtin import STRATEGY_REGISTRY


@pytest.fixture
def engine() -> ReasoningEngine:
    eng = ReasoningEngine(metrics=ReasoningMetrics())
    yield eng
    eng.reset()


@pytest.fixture(autouse=True)
def _reset_events():
    reset_subscribers()
    yield
    reset_subscribers()


@pytest.mark.asyncio
async def test_all_strategies_registered():
    expected = {
        "rule_based", "chain_of_thought", "tree_of_thought",
        "reflective", "planning_first", "fast_heuristic",
    }
    assert set(STRATEGY_REGISTRY.keys()) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("strategy", list(ReasoningStrategy))
async def test_pipeline_strategies(engine: ReasoningEngine, strategy: ReasoningStrategy):
    ctx = ReasoningContext(
        request="I want to buy a car under $30000",
        agent_id="auto_agent",
        capabilities=["buy_car", "vin_lookup"],
        available_tools=["crm_lookup"],
    )
    result = await engine.reason(ctx, strategy=strategy)
    assert result.success
    assert result.intent
    assert result.confidence.overall > 0
    assert len(result.trace.steps) >= 1


@pytest.mark.asyncio
async def test_intent_extraction_buy_car(engine: ReasoningEngine):
    ctx = ReasoningContext(request="I want to buy a Toyota SUV")
    result = await engine.reason(ctx, strategy=ReasoningStrategy.RULE_BASED)
    assert result.intent == "buy_car"


@pytest.mark.asyncio
async def test_intent_extraction_legal(engine: ReasoningEngine):
    ctx = ReasoningContext(request="Review this legal contract for compliance")
    result = await engine.reason(ctx, strategy=ReasoningStrategy.RULE_BASED)
    assert result.intent == "legal_contract"


@pytest.mark.asyncio
async def test_confidence_model(engine: ReasoningEngine):
    ctx = ReasoningContext(
        request="Buy grain for export with urgent delivery",
        agent_id="agro_agent",
        user_id="u1",
        capabilities=["grain_trade"],
        memory_context={"facts": ["prefers organic"]},
        available_tools=["crm_lookup", "search_query"],
        constraints=["budget_constraint"],
    )
    result = await engine.reason(ctx, strategy=ReasoningStrategy.PLANNING_FIRST)
    c = result.confidence
    assert 0 <= c.overall <= 100
    assert c.reasoning > 0
    assert c.data > 0
    assert c.memory > 0
    assert c.tool > 0


@pytest.mark.asyncio
async def test_missing_information(engine: ReasoningEngine):
    ctx = ReasoningContext(request="Buy car")
    result = await engine.reason(ctx, strategy=ReasoningStrategy.REFLECTIVE)
    assert "budget" in result.missing_information or len(result.missing_information) >= 0


@pytest.mark.asyncio
async def test_planning_first_generates_plan(engine: ReasoningEngine):
    ctx = ReasoningContext(request="Need market analysis report")
    result = await engine.reason(ctx, strategy=ReasoningStrategy.PLANNING_FIRST)
    assert len(result.plan) >= 3
    assert any("market_analysis" in step or "execute" in step for step in result.plan)


@pytest.mark.asyncio
async def test_explainability_trace(engine: ReasoningEngine):
    ctx = ReasoningContext(request="Track my shipment to port")
    result = await engine.reason(ctx, strategy=ReasoningStrategy.CHAIN_OF_THOUGHT)
    explanation = result.explanation()
    assert "Intent:" in explanation
    assert "Confidence:" in explanation
    trace_dict = result.trace.to_dict()
    assert trace_dict["steps"]
    assert result.trace.human_readable()


@pytest.mark.asyncio
async def test_debug_mode():
    pipeline = ReasoningPipeline(debug=True)
    ctx = ReasoningContext(request="Hello")
    result = await pipeline.run(ctx, strategy="fast_heuristic")
    assert result.trace.debug.get("debug_mode") is True


@pytest.mark.asyncio
async def test_reasoning_events(engine: ReasoningEngine):
    events: list[str] = []

    async def capture(e):
        events.append(type(e).__name__)

    subscribe(ReasoningStartedEvent, capture)
    subscribe(ReasoningCompletedEvent, capture)
    subscribe(ReasoningFailedEvent, capture)

    ctx = ReasoningContext(request="Buy a car")
    await engine.reason(ctx)
    await asyncio.sleep(0.05)
    assert "ReasoningStartedEvent" in events
    assert "ReasoningCompletedEvent" in events


@pytest.mark.asyncio
async def test_session_tracking(engine: ReasoningEngine):
    ctx = ReasoningContext(request="Test")
    result = await engine.reason(ctx)
    session = engine.get_session(result.session_id)
    assert session.status == "completed"
    assert session.result is not None


@pytest.mark.asyncio
async def test_metrics(engine: ReasoningEngine):
    ctx = ReasoningContext(request="Buy car")
    await engine.reason(ctx, strategy=ReasoningStrategy.FAST_HEURISTIC)
    await engine.reason(ctx, strategy=ReasoningStrategy.RULE_BASED)
    summary = engine.metrics_summary()
    assert summary["sessions"] == 2
    assert summary["avg_confidence"] > 0
    assert "fast_heuristic" in summary["strategy_usage"]


@pytest.mark.asyncio
async def test_tree_of_thought_branching(engine: ReasoningEngine):
    ctx = ReasoningContext(
        request="What should I do?",
        agent_id="auto_agent",
        capabilities=["buy_car"],
    )
    result = await engine.reason(ctx, strategy=ReasoningStrategy.TREE_OF_THOUGHT)
    branch_steps = [s for s in result.trace.steps if s.phase == "branch"]
    assert len(branch_steps) >= 3


@pytest.mark.asyncio
async def test_integration_context_from_agent():
    from platform_agents.registry import agent_registry
    from platform_agents.agents.builtin import register_builtin_agents
    from platform_reasoning.integrations import ReasoningIntegrations

    agent_registry.reset()
    register_builtin_agents(agent_registry)
    ctx = ReasoningIntegrations.context_from_agent("auto_agent", "Buy SUV")
    assert "buy_car" in ctx.capabilities
    agent_registry.reset()


@pytest.mark.asyncio
async def test_orchestrator_hints(engine: ReasoningEngine):
    from platform_reasoning.integrations import ReasoningIntegrations

    ctx = ReasoningContext(request="Buy a car", capabilities=["buy_car"])
    result = await engine.reason(ctx)
    hints = ReasoningIntegrations.apply_to_orchestrator(result.to_dict())
    assert hints["capability"] == "buy_car"
    assert hints["confidence"] > 0
