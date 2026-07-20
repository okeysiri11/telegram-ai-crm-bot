"""Tests — Platform Decision Engine (Sprint 4.3)."""

from __future__ import annotations

import asyncio

import pytest

from platform_decision.exceptions import DecisionError
from platform_decision.metrics import DecisionMetrics
from platform_decision.models import DecisionCandidate, DecisionContext, DecisionCriteria, DecisionStrategyType
from platform_decision.decision_engine import DecisionEngine
from platform_decision.decision_events import DecisionCompletedEvent, DecisionStartedEvent
from platform_decision.integrations import DecisionIntegrations
from platform_decision.policies import DecisionPolicy, policy_registry
from platform_decision.strategies.builtin import STRATEGY_REGISTRY
from events.event_bus import reset_subscribers, subscribe


def _candidate(
    cid: str,
    name: str,
    *,
    cost: float = 10.0,
    duration: float = 1000.0,
    risk: float = 10.0,
    confidence: float = 80.0,
    capability: str | None = None,
    agent_id: str | None = None,
) -> DecisionCandidate:
    return DecisionCandidate(
        candidate_id=cid,
        name=name,
        capability=capability,
        agent_id=agent_id,
        criteria=DecisionCriteria(
            execution_cost=cost,
            estimated_duration_ms=duration,
            risk_level=risk,
            confidence_score=confidence,
            tool_availability=90.0,
            agent_availability=90.0,
            resource_consumption=20.0,
            business_priority=50.0,
            user_preference=50.0,
        ),
    )


def _ctx(**kwargs) -> DecisionContext:
    defaults = {
        "request": "Buy a Toyota SUV",
        "agent_id": "auto_agent",
        "candidates": [
            _candidate("c1", "Low cost route", cost=5.0, duration=3000.0, risk=30.0, confidence=70.0, capability="buy_car", agent_id="auto_agent"),
            _candidate("c2", "Fast route", cost=20.0, duration=500.0, risk=15.0, confidence=85.0, capability="vehicle_inspection", agent_id="auto_agent"),
            _candidate("c3", "Safe route", cost=15.0, duration=1500.0, risk=5.0, confidence=90.0, capability="auto_financing", agent_id="auto_agent"),
        ],
        "available_agents": ["auto_agent"],
        "available_tools": ["crm_lookup"],
        "reasoning_result": {"intent": "buy_car", "confidence": {"overall": 75.0}},
    }
    defaults.update(kwargs)
    return DecisionContext(**defaults)


@pytest.fixture
def engine() -> DecisionEngine:
    eng = DecisionEngine(metrics=DecisionMetrics())
    yield eng
    eng.reset()


@pytest.fixture(autouse=True)
def _reset_events():
    reset_subscribers()
    yield
    reset_subscribers()


@pytest.mark.asyncio
@pytest.mark.parametrize("strategy", list(DecisionStrategyType))
async def test_all_strategies(engine: DecisionEngine, strategy: DecisionStrategyType):
    result = await engine.decide(_ctx(), strategy=strategy)
    assert result.selected is not None
    assert result.confidence >= 0
    assert result.decision_time_ms >= 0


@pytest.mark.asyncio
async def test_cost_optimization_prefers_low_cost(engine: DecisionEngine):
    ctx = _ctx(candidates=[
        _candidate("c1", "Cheap", cost=1.0, duration=10000.0, risk=80.0, confidence=50.0),
        _candidate("c2", "Expensive", cost=100.0, duration=100.0, risk=80.0, confidence=50.0),
    ])
    result = await engine.decide(ctx, strategy=DecisionStrategyType.COST_OPTIMIZATION)
    assert result.selected.candidate_id == "c1"


@pytest.mark.asyncio
async def test_time_optimization_prefers_fast(engine: DecisionEngine):
    ctx = _ctx(candidates=[
        _candidate("c1", "Slow", cost=50.0, duration=10000.0, risk=50.0, confidence=50.0),
        _candidate("c2", "Fast", cost=50.0, duration=100.0, risk=50.0, confidence=50.0),
    ])
    result = await engine.decide(ctx, strategy=DecisionStrategyType.TIME_OPTIMIZATION)
    assert result.selected.candidate_id == "c2"


@pytest.mark.asyncio
async def test_risk_aware_prefers_safe(engine: DecisionEngine):
    result = await engine.decide(_ctx(), strategy=DecisionStrategyType.RISK_AWARE)
    assert result.selected.candidate_id == "c3"


@pytest.mark.asyncio
async def test_confidence_aware(engine: DecisionEngine):
    result = await engine.decide(_ctx(), strategy=DecisionStrategyType.CONFIDENCE_AWARE)
    assert result.selected.candidate_id == "c3"


@pytest.mark.asyncio
async def test_rule_based_matches_intent(engine: DecisionEngine):
    result = await engine.decide(_ctx(), strategy=DecisionStrategyType.RULE_BASED)
    assert result.selected.capability == "buy_car"


@pytest.mark.asyncio
async def test_no_candidates_raises(engine: DecisionEngine):
    with pytest.raises(Exception):
        await engine.decide(DecisionContext(request="test", candidates=[]))


@pytest.mark.asyncio
async def test_explanation_and_trace(engine: DecisionEngine):
    result = await engine.decide(_ctx())
    assert "Selected:" in result.explanation()
    assert result.trace is not None
    assert len(result.trace.steps) >= 4
    assert result.alternatives


@pytest.mark.asyncio
async def test_metrics_recorded(engine: DecisionEngine):
    await engine.decide(_ctx())
    summary = engine.metrics_summary()
    assert summary["decisions"] == 1
    assert summary["avg_confidence"] > 0
    assert summary["policy_usage"].get("balanced") == 1


@pytest.mark.asyncio
async def test_custom_policy(engine: DecisionEngine):
    engine.register_policy(
        DecisionPolicy(
            policy_id="custom",
            name="Custom",
            weights={"business_priority": 0.9, "execution_cost": 0.1},
        )
    )
    ctx = _ctx()
    ctx.candidates[0].criteria.business_priority = 10.0
    ctx.candidates[2].criteria.business_priority = 95.0
    result = await engine.decide(ctx, policy_id="custom")
    assert result.policy_id == "custom"


@pytest.mark.asyncio
async def test_policy_not_found(engine: DecisionEngine):
    with pytest.raises(DecisionError):
        await engine.decide(_ctx(), policy_id="missing")


@pytest.mark.asyncio
async def test_fallback_strategy(engine: DecisionEngine):
    result = await engine.decide(_ctx(), strategy=DecisionStrategyType.FALLBACK)
    assert result.selected.candidate_id == "c1"


@pytest.mark.asyncio
async def test_decision_events(engine: DecisionEngine):
    started: list[DecisionStartedEvent] = []
    completed: list[DecisionCompletedEvent] = []

    async def capture_started(e: DecisionStartedEvent) -> None:
        started.append(e)

    async def capture_completed(e: DecisionCompletedEvent) -> None:
        completed.append(e)

    subscribe(DecisionStartedEvent, capture_started)
    subscribe(DecisionCompletedEvent, capture_completed)

    await engine.decide(_ctx())
    await asyncio.sleep(0.05)

    assert len(started) == 1
    assert len(completed) == 1
    assert completed[0].selected_candidate_id


@pytest.mark.asyncio
async def test_integrations_candidates_from_capabilities():
    caps = DecisionIntegrations.candidates_from_capabilities(["buy_car", "inspect"], agent_id="auto_agent")
    assert len(caps) == 2
    assert caps[0].capability == "buy_car"


@pytest.mark.asyncio
async def test_decide_for_agent(engine: DecisionEngine):
    result = await engine.decide_for_agent("auto_agent", "Buy SUV", use_planning=False)
    assert result.success
    assert result.selected is not None


@pytest.mark.asyncio
async def test_orchestrator_routing():
    from platform_decision.integrations import decision_integrations

    route = decision_integrations.orchestrator_routing(
        {"decision_id": "d1", "selected": {"capability": "buy_car", "agent_id": "auto_agent"}, "confidence": 88.0}
    )
    assert route["capability"] == "buy_car"


@pytest.mark.asyncio
async def test_strategy_registry_covers_all_types():
    for st in DecisionStrategyType:
        assert st.value in STRATEGY_REGISTRY


@pytest.mark.asyncio
async def test_trace_stored(engine: DecisionEngine):
    result = await engine.decide(_ctx())
    stored = engine.get_trace(result.decision_id)
    assert stored is not None
    assert stored.decision_id == result.decision_id


@pytest.mark.asyncio
async def test_to_dict_machine_readable(engine: DecisionEngine):
    result = await engine.decide(_ctx())
    d = result.to_dict()
    assert d["selected"]["candidate_id"]
    assert d["trace"]["steps"]
    assert "alternatives_count" in d
