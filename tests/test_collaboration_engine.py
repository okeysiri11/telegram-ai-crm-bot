"""Tests — Platform Multi-Agent Collaboration Engine (Sprint 4.5)."""

from __future__ import annotations

import asyncio

import pytest

from events.event_bus import reset_subscribers, subscribe
from platform_collaboration.collaboration_engine import CollaborationEngine
from platform_collaboration.collaboration_events import (
    AgentJoinedEvent,
    CollaborationCompletedEvent,
    CollaborationStartedEvent,
    ConsensusReachedEvent,
    TaskDelegatedEvent,
)
from platform_collaboration.conflict_resolver import ConflictResolver
from platform_collaboration.consensus_engine import ConsensusEngine
from platform_collaboration.coordination import STRATEGY_REGISTRY
from platform_collaboration.exceptions import SessionNotFoundError
from platform_collaboration.metrics import CollaborationMetrics
from platform_collaboration.models import (
    AgentMessage,
    AgentParticipant,
    CollaborationMode,
    CollaborationRole,
    CollaborationSession,
    CollaborationTask,
    ConsensusModel,
    CoordinationStrategy,
    MessageType,
    SharedContext,
)
from platform_collaboration.negotiation_engine import NegotiationEngine
from platform_collaboration.pipeline import CollaborationPipeline


def _participant(agent_id: str, caps: list[str] | None = None, **kwargs) -> AgentParticipant:
    return AgentParticipant(agent_id=agent_id, capabilities=caps or ["buy_car"], **kwargs)


@pytest.fixture
def engine() -> CollaborationEngine:
    eng = CollaborationEngine(metrics=CollaborationMetrics())
    yield eng
    eng.reset()


@pytest.fixture(autouse=True)
def _reset_events():
    reset_subscribers()
    yield
    reset_subscribers()


def _tasks() -> list[CollaborationTask]:
    return [
        CollaborationTask(name="Search vehicles", capability="buy_car", priority=80.0),
        CollaborationTask(name="Inspect vehicle", capability="vehicle_inspection", priority=70.0),
        CollaborationTask(name="Arrange financing", capability="auto_financing", priority=60.0),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", list(CollaborationMode))
async def test_all_collaboration_modes(engine: CollaborationEngine, mode: CollaborationMode):
    result = await engine.collaborate(
        "Buy a Toyota SUV",
        ["auto_agent", "finance_agent"],
        mode=mode,
        supervisor_id="auto_agent",
        tasks=_tasks(),
    )
    assert result.session.mode == mode
    assert result.session.collaboration_time_ms >= 0


@pytest.mark.asyncio
async def test_supervisor_worker_collaboration(engine: CollaborationEngine):
    result = await engine.collaborate(
        "Buy a Toyota SUV",
        ["auto_agent", "finance_agent"],
        mode=CollaborationMode.SUPERVISOR_WORKER,
        supervisor_id="auto_agent",
        tasks=_tasks(),
    )
    assert result.success
    assert len(result.completed_tasks) >= 1
    assert result.delegations >= 1


@pytest.mark.asyncio
async def test_one_to_one_mode(engine: CollaborationEngine):
    result = await engine.collaborate(
        "Quick lookup",
        ["auto_agent", "finance_agent"],
        mode=CollaborationMode.ONE_TO_ONE,
        tasks=[CollaborationTask(name="Lookup", capability="buy_car")],
    )
    assert result.session.mode == CollaborationMode.ONE_TO_ONE


@pytest.mark.asyncio
async def test_peer_to_peer(engine: CollaborationEngine):
    result = await engine.collaborate(
        "Collaborative research",
        ["auto_agent", "finance_agent", "legal_agent"],
        mode=CollaborationMode.PEER_TO_PEER,
        strategy=CoordinationStrategy.PEER_CONSENSUS,
        tasks=_tasks(),
    )
    assert len(result.consensus_results) >= 1


@pytest.mark.asyncio
async def test_hierarchical_coordination(engine: CollaborationEngine):
    result = await engine.collaborate(
        "Enterprise purchase",
        ["auto_agent", "finance_agent", "legal_agent"],
        mode=CollaborationMode.HIERARCHICAL,
        strategy=CoordinationStrategy.ROLE_BASED,
        supervisor_id="auto_agent",
        tasks=_tasks(),
    )
    assert result.success


@pytest.mark.asyncio
async def test_negotiation_engine():
    session = CollaborationSession(supervisor_id="auto_agent")
    session.participants = {
        "auto_agent": _participant("auto_agent", ["buy_car", "vehicle_inspection"], confidence=90.0),
        "finance_agent": _participant("finance_agent", ["auto_financing"], confidence=80.0),
    }
    task = CollaborationTask(name="Finance", capability="auto_financing")
    neg = NegotiationEngine().negotiate_task_ownership(session, task)
    assert neg.success
    assert neg.owner_id == "finance_agent"


@pytest.mark.asyncio
async def test_consensus_weighted_voting():
    session = CollaborationSession(consensus_model=ConsensusModel.WEIGHTED_VOTING)
    session.participants = {
        "a1": _participant("a1", weight=2.0),
        "a2": _participant("a2", weight=1.0),
    }
    result = ConsensusEngine().reach_consensus(
        session,
        proposal="approve",
        votes={"a1": "approve", "a2": "reject"},
        model=ConsensusModel.WEIGHTED_VOTING,
    )
    assert result.success
    assert result.decision == "approve"


@pytest.mark.asyncio
async def test_consensus_supervisor_override():
    session = CollaborationSession(supervisor_id="sup", consensus_model=ConsensusModel.SUPERVISOR_OVERRIDE)
    session.participants = {"sup": _participant("sup", confidence=95.0)}
    result = ConsensusEngine().reach_consensus(session, proposal="proceed", model=ConsensusModel.SUPERVISOR_OVERRIDE)
    assert result.decision == "proceed"


@pytest.mark.asyncio
async def test_consensus_confidence_based():
    session = CollaborationSession()
    session.participants = {
        "a1": _participant("a1", confidence=90.0),
        "a2": _participant("a2", confidence=30.0),
    }
    result = ConsensusEngine().reach_consensus(
        session,
        proposal="go",
        votes={"a1": "go", "a2": "stop"},
        model=ConsensusModel.CONFIDENCE_BASED,
    )
    assert result.decision == "go"


@pytest.mark.asyncio
async def test_conflict_detection_and_resolution():
    session = CollaborationSession(supervisor_id="auto_agent")
    session.participants = {
        "auto_agent": _participant("auto_agent", ["buy_car"]),
        "finance_agent": _participant("finance_agent", ["auto_financing"]),
    }
    tasks = [
        CollaborationTask(task_id=f"t{i}", name=f"Task {i}", capability="buy_car", owner_id="auto_agent")
        for i in range(5)
    ]
    resolver = ConflictResolver()
    conflicts = resolver.detect_conflicts(session, tasks)
    assert len(conflicts) >= 1
    assert resolver.resolve(session, conflicts[0], tasks)


@pytest.mark.asyncio
async def test_shared_context():
    ctx = SharedContext(goal="Buy SUV", session_id="s1")
    ctx.announce_capability("auto_agent", ["buy_car"])
    ctx.merge_result("auto_agent", {"vehicles": 3})
    assert ctx.capabilities["auto_agent"] == ["buy_car"]
    assert ctx.intermediate_results["auto_agent"]["vehicles"] == 3


@pytest.mark.asyncio
async def test_agent_messages(engine: CollaborationEngine):
    result = await engine.collaborate(
        "Test",
        ["auto_agent"],
        tasks=[CollaborationTask(name="T1", capability="buy_car")],
    )
    sid = result.session.session_id
    msg = await engine.broadcast_progress(sid, "auto_agent", 0.5, "half done")
    assert msg.message_type == MessageType.PROGRESS_UPDATE
    shared = await engine.share_result(sid, "auto_agent", {"data": "value"})
    assert shared.message_type == MessageType.INTERMEDIATE_RESULT


@pytest.mark.asyncio
async def test_collaboration_events(engine: CollaborationEngine):
    events: list[str] = []

    async def capture(e):
        events.append(type(e).__name__)

    subscribe(CollaborationStartedEvent, capture)
    subscribe(AgentJoinedEvent, capture)
    subscribe(TaskDelegatedEvent, capture)
    subscribe(ConsensusReachedEvent, capture)
    subscribe(CollaborationCompletedEvent, capture)

    await engine.collaborate(
        "Buy SUV",
        ["auto_agent", "finance_agent"],
        tasks=_tasks(),
    )
    await asyncio.sleep(0.05)

    assert "CollaborationStartedEvent" in events
    assert "CollaborationCompletedEvent" in events


@pytest.mark.asyncio
async def test_metrics_recorded(engine: CollaborationEngine):
    await engine.collaborate("Goal", ["auto_agent"], tasks=[CollaborationTask(name="T", capability="buy_car")])
    summary = engine.metrics_summary()
    assert summary["collaborations"] == 1
    assert summary["total_delegations"] >= 1


@pytest.mark.asyncio
async def test_session_retrieval(engine: CollaborationEngine):
    result = await engine.collaborate("Goal", ["auto_agent"], tasks=[CollaborationTask(name="T", capability="buy_car")])
    session = engine.get_session(result.session.session_id)
    assert session.status == "completed"


@pytest.mark.asyncio
async def test_session_not_found(engine: CollaborationEngine):
    with pytest.raises(SessionNotFoundError):
        engine.get_session("missing")


@pytest.mark.asyncio
async def test_strategy_registry():
    for strategy in CoordinationStrategy:
        assert strategy.value in STRATEGY_REGISTRY


@pytest.mark.asyncio
async def test_integrations_orchestrator_routing():
    from platform_collaboration.integrations import collaboration_integrations

    session = CollaborationSession(goal="Buy SUV", mode=CollaborationMode.SUPERVISOR_WORKER, supervisor_id="auto_agent")
    session.participants["auto_agent"] = _participant("auto_agent")
    route = collaboration_integrations.orchestrator_routing(session)
    assert route["goal"] == "Buy SUV"
    assert route["supervisor_id"] == "auto_agent"


@pytest.mark.asyncio
async def test_parallel_strategy():
    session = CollaborationSession()
    session.participants = {"a1": _participant("a1"), "a2": _participant("a2")}
    tasks = [
        CollaborationTask(name="Independent", capability="buy_car"),
        CollaborationTask(name="Dependent", capability="auto_financing", depends_on=["dep"]),
    ]
    tasks[0].task_id = "dep"
    ordered = STRATEGY_REGISTRY["parallel"].order_tasks(session, tasks)
    assert ordered[0].name == "Independent"


@pytest.mark.asyncio
async def test_to_dict_machine_readable(engine: CollaborationEngine):
    result = await engine.collaborate("Goal", ["auto_agent"], tasks=[CollaborationTask(name="T", capability="buy_car")])
    d = result.to_dict()
    assert d["session"]["session_id"]
    assert "completed_tasks" in d
