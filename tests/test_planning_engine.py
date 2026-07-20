"""Tests — Platform Planning Engine (Sprint 4.2)."""

from __future__ import annotations

import asyncio

import pytest

from platform_planning.metrics import PlanningMetrics
from platform_planning.models import PlanningContext, PlanningStrategy, PlanStepStatus
from platform_planning.planning_engine import PlanningEngine
from platform_planning.replanning import ReplanningEngine
from platform_planning.strategies.builtin import STRATEGY_REGISTRY
from platform_planning.validator import PlanValidator


@pytest.fixture
def engine() -> PlanningEngine:
    eng = PlanningEngine(metrics=PlanningMetrics())
    yield eng
    eng.reset()


def _ctx(**kwargs) -> PlanningContext:
    defaults = {
        "goal": "Buy a Toyota SUV",
        "agent_id": "auto_agent",
        "intent": "buy_car",
        "capabilities": ["buy_car", "vehicle_inspection", "auto_financing"],
        "available_tools": ["crm_lookup"],
        "available_agents": ["auto_agent"],
        "permissions": ["execute"],
    }
    defaults.update(kwargs)
    return PlanningContext(**defaults)


@pytest.mark.asyncio
@pytest.mark.parametrize("strategy", list(PlanningStrategy))
async def test_all_strategies(engine: PlanningEngine, strategy: PlanningStrategy):
    result = await engine.plan(_ctx(), strategy=strategy)
    assert result.plan.step_count >= 1
    assert result.planning_time_ms >= 0


@pytest.mark.asyncio
async def test_sequential_plan(engine: PlanningEngine):
    result = await engine.plan(_ctx(), strategy=PlanningStrategy.SEQUENTIAL)
    assert result.success
    assert result.plan.step_count >= 3
    step_ids = [s.step_id for s in result.plan.steps]
    assert step_ids.index("step_search") < step_ids.index("step_inspect")


@pytest.mark.asyncio
async def test_parallel_plan(engine: PlanningEngine):
    result = await engine.plan(_ctx(), strategy=PlanningStrategy.PARALLEL)
    parallel_steps = [s for s in result.plan.steps if s.parallel_group]
    assert len(parallel_steps) >= 1


@pytest.mark.asyncio
async def test_hierarchical_plan(engine: PlanningEngine):
    result = await engine.plan(_ctx(), strategy=PlanningStrategy.HIERARCHICAL)
    assert result.plan.steps[0].step_id == "step_parent"


@pytest.mark.asyncio
async def test_goal_decomposition(engine: PlanningEngine):
    result = await engine.plan(_ctx(), strategy=PlanningStrategy.GOAL_DECOMPOSITION)
    assert any(s.step_id == "step_decompose" for s in result.plan.steps)


@pytest.mark.asyncio
async def test_dependency_aware_assigns_tools(engine: PlanningEngine):
    result = await engine.plan(_ctx(), strategy=PlanningStrategy.DEPENDENCY_AWARE)
    assert result.success
    assert result.workflow_definition.get("steps")


@pytest.mark.asyncio
async def test_circular_dependency_detection():
    validator = PlanValidator()
    from platform_planning.models import ExecutionPlan, PlanStep

    plan = ExecutionPlan(
        goal="test",
        steps=[
            PlanStep(step_id="a", name="A", depends_on=["b"]),
            PlanStep(step_id="b", name="B", depends_on=["a"]),
        ],
    )
    with pytest.raises(Exception):
        validator.validate(plan, _ctx())


@pytest.mark.asyncio
async def test_missing_capability_detection():
    validator = PlanValidator()
    from platform_planning.models import ExecutionPlan, PlanStep

    plan = ExecutionPlan(
        goal="test",
        steps=[PlanStep(step_id="s1", name="S", capability="nonexistent_cap")],
    )
    with pytest.raises(Exception):
        validator.validate(plan, _ctx(capabilities=["buy_car"]))


@pytest.mark.asyncio
async def test_replanning_reuses_completed(engine: PlanningEngine):
    result = await engine.plan(_ctx())
    plan = result.plan
    engine.mark_step_completed(plan.plan_id, plan.steps[0].step_id, {"done": True})

    new_plan = await engine.replan(plan.plan_id, plan.steps[1].step_id, _ctx(), error="timeout")
    assert new_plan.status in ("replanned", "replanned_with_warnings")
    assert plan.steps[0].step_id in new_plan.completed_steps or any(
        s.step_id == plan.steps[0].step_id and s.status == PlanStepStatus.COMPLETED for s in new_plan.steps
    )


@pytest.mark.asyncio
async def test_workflow_definition(engine: PlanningEngine):
    result = await engine.plan(_ctx())
    wf = result.workflow_definition
    assert wf["plan_id"] == result.plan.plan_id
    assert len(wf["steps"]) == result.plan.step_count


@pytest.mark.asyncio
async def test_metrics(engine: PlanningEngine):
    await engine.plan(_ctx())
    await engine.plan(_ctx(goal="Legal contract review"), strategy=PlanningStrategy.SEQUENTIAL)
    summary = engine.metrics_summary()
    assert summary["plans"] == 2
    assert summary["avg_plan_size"] > 0


@pytest.mark.asyncio
async def test_all_strategies_registered():
    assert len(STRATEGY_REGISTRY) == 6


@pytest.mark.asyncio
async def test_legal_goal_planning(engine: PlanningEngine):
    result = await engine.plan(
        _ctx(goal="Review legal contract", intent="legal_contract", capabilities=["legal_contract", "compliance_check"]),
        strategy=PlanningStrategy.SEQUENTIAL,
    )
    assert result.success
    caps = [s.capability for s in result.plan.steps if s.capability]
    assert "legal_contract" in caps


@pytest.mark.asyncio
async def test_plan_for_agent(engine: PlanningEngine):
    from platform_agents.registry import agent_registry
    from platform_agents.agents.builtin import register_builtin_agents

    agent_registry.reset()
    register_builtin_agents(agent_registry)
    result = await engine.plan_for_agent("auto_agent", "Buy SUV", use_reasoning=False)
    assert result.plan.step_count >= 1
    agent_registry.reset()


@pytest.mark.asyncio
async def test_replanning_engine_mark_steps():
    from platform_planning.models import ExecutionPlan, PlanStep

    repl = ReplanningEngine()
    plan = ExecutionPlan(steps=[PlanStep(step_id="s1", name="S1"), PlanStep(step_id="s2", name="S2")])
    repl.mark_step_completed(plan, "s1", {"ok": True})
    assert plan.steps[0].status == PlanStepStatus.COMPLETED
    repl.mark_step_failed(plan, "s2")
    assert plan.steps[1].status == PlanStepStatus.FAILED
