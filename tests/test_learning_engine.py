"""Tests — Platform Learning & Feedback Engine (Sprint 4.4)."""

from __future__ import annotations

import asyncio

import pytest

from events.event_bus import reset_subscribers, subscribe
from platform_learning.exceptions import FeedbackValidationError, SessionNotFoundError
from platform_learning.experience_store import ExperienceStore
from platform_learning.feedback_collector import FeedbackCollector
from platform_learning.learning_engine import LearningEngine
from platform_learning.learning_events import FeedbackReceivedEvent, LearningCycleCompletedEvent, LearningCycleStartedEvent
from platform_learning.metrics import LearningMetrics
from platform_learning.models import (
    FeedbackCategory,
    FeedbackRecord,
    FeedbackSentiment,
    FeedbackSource,
    LearningContext,
    LearningEvent,
    RecommendationType,
)
from platform_learning.pattern_analyzer import PatternAnalyzer
from platform_learning.pipeline import LearningPipeline
from platform_learning.recommendation_engine import RecommendationEngine


@pytest.fixture
def engine() -> LearningEngine:
    store = ExperienceStore()
    eng = LearningEngine(
        metrics=LearningMetrics(),
        pipeline=LearningPipeline(
            collector=FeedbackCollector(store=store),
            store=store,
            analyzer=PatternAnalyzer(store=store),
            recommender=RecommendationEngine(store=store),
        ),
    )
    yield eng
    eng.reset()


@pytest.fixture(autouse=True)
def _reset_events():
    reset_subscribers()
    yield
    reset_subscribers()


def _feedback(**kwargs) -> FeedbackRecord:
    defaults = {
        "sentiment": FeedbackSentiment.POSITIVE,
        "confidence_score": 85.0,
        "category": FeedbackCategory.WORKFLOW,
        "source": FeedbackSource.WORKFLOW_RESULT,
        "message": "Workflow completed",
        "agent_id": "auto_agent",
        "workflow_id": "wf_1",
    }
    defaults.update(kwargs)
    return FeedbackRecord(**defaults)


@pytest.mark.asyncio
async def test_collect_workflow_feedback(engine: LearningEngine):
    fb = await engine.collect_feedback(
        _feedback(sentiment=FeedbackSentiment.POSITIVE, workflow_id="wf_ok")
    )
    assert fb.feedback_id
    assert fb.sentiment == FeedbackSentiment.POSITIVE


@pytest.mark.asyncio
async def test_collect_human_feedback(engine: LearningEngine):
    from platform_learning.feedback_collector import feedback_collector

    fb = feedback_collector.collect_human_feedback(
        "Great job!",
        sentiment=FeedbackSentiment.POSITIVE,
        agent_id="auto_agent",
    )
    assert fb.source == FeedbackSource.HUMAN_FEEDBACK


@pytest.mark.asyncio
async def test_collect_error_report(engine: LearningEngine):
    from platform_learning.feedback_collector import feedback_collector

    fb = feedback_collector.collect_error_report("Timeout error", agent_id="auto_agent", severity=90.0)
    assert fb.sentiment == FeedbackSentiment.NEGATIVE
    assert fb.severity == 90.0


@pytest.mark.asyncio
async def test_learning_cycle(engine: LearningEngine):
    ctx = LearningContext(
        agent_id="auto_agent",
        feedback=[
            _feedback(workflow_id="wf_1"),
            _feedback(workflow_id="wf_2"),
            _feedback(
                sentiment=FeedbackSentiment.NEGATIVE,
                message="Failed step",
                workflow_id="wf_3",
                category=FeedbackCategory.WORKFLOW,
            ),
            _feedback(
                sentiment=FeedbackSentiment.NEGATIVE,
                message="Failed step",
                workflow_id="wf_4",
                category=FeedbackCategory.WORKFLOW,
            ),
        ],
    )
    result = await engine.learn(ctx)
    assert result.success
    assert result.session.status == "completed"
    assert result.insights["feedback_volume"] >= 4


@pytest.mark.asyncio
async def test_pattern_detection(engine: LearningEngine):
    ctx = LearningContext(
        agent_id="auto_agent",
        feedback=[
            _feedback(workflow_id=f"wf_{i}") for i in range(3)
        ],
    )
    result = await engine.learn(ctx)
    assert len(result.success_patterns) >= 1


@pytest.mark.asyncio
async def test_failure_pattern_detection(engine: LearningEngine):
    ctx = LearningContext(
        agent_id="auto_agent",
        feedback=[
            FeedbackRecord(
                sentiment=FeedbackSentiment.NEGATIVE,
                message="Same error occurred",
                category=FeedbackCategory.PLANNING,
                source=FeedbackSource.ERROR_REPORT,
                agent_id="auto_agent",
            )
            for _ in range(3)
        ],
    )
    result = await engine.learn(ctx)
    assert len(result.failure_patterns) >= 1


@pytest.mark.asyncio
async def test_recommendations_generated(engine: LearningEngine):
    ctx = LearningContext(
        agent_id="auto_agent",
        feedback=[
            FeedbackRecord(
                sentiment=FeedbackSentiment.NEGATIVE,
                message="Planning failed again",
                category=FeedbackCategory.PLANNING,
                source=FeedbackSource.ERROR_REPORT,
                agent_id="auto_agent",
            )
            for _ in range(2)
        ],
    )
    result = await engine.learn(ctx)
    planning_recs = [r for r in result.recommendations if r.recommendation_type == RecommendationType.PLANNING_STRATEGY]
    assert len(planning_recs) >= 1


@pytest.mark.asyncio
async def test_repeated_failure_recommendation(engine: LearningEngine):
    msg = "Connection timeout on CRM lookup"
    ctx = LearningContext(
        agent_id="auto_agent",
        feedback=[
            FeedbackRecord(
                sentiment=FeedbackSentiment.NEGATIVE,
                message=msg,
                category=FeedbackCategory.TOOL,
                source=FeedbackSource.ERROR_REPORT,
                tool_id="crm_lookup",
                agent_id="auto_agent",
            )
            for _ in range(3)
        ],
    )
    result = await engine.learn(ctx)
    repeated = [r for r in result.recommendations if r.recommendation_type == RecommendationType.REPEATED_FAILURE]
    assert len(repeated) >= 1


@pytest.mark.asyncio
async def test_experience_store(engine: LearningEngine):
    from platform_learning.feedback_collector import FeedbackCollector
    from platform_learning.experience_store import ExperienceStore

    store = ExperienceStore()
    collector = FeedbackCollector(store=store)
    collector.collect_workflow_result("wf_1", success=True, agent_id="auto_agent")
    collector.collect_workflow_result("wf_2", success=False, agent_id="auto_agent")
    assert store.count() >= 2
    snap = store.snapshot()
    assert len(snap["workflows_success"]) >= 1
    assert len(snap["workflows_failed"]) >= 1


@pytest.mark.asyncio
async def test_recommendation_acceptance(engine: LearningEngine):
    ctx = LearningContext(agent_id="auto_agent", feedback=[_feedback()])
    result = await engine.learn(ctx)
    if result.recommendations:
        rec_id = result.recommendations[0].recommendation_id
        engine.accept_recommendation(rec_id)
        summary = engine.metrics_summary()
        assert summary["recommendation_acceptance_rate"] == 1.0


@pytest.mark.asyncio
async def test_metrics_recorded(engine: LearningEngine):
    await engine.learn(LearningContext(agent_id="auto_agent", feedback=[_feedback(), _feedback(workflow_id="wf_2")]))
    summary = engine.metrics_summary()
    assert summary["learning_cycles"] == 1
    assert summary["feedback_volume"] >= 2


@pytest.mark.asyncio
async def test_session_retrieval(engine: LearningEngine):
    result = await engine.learn(LearningContext(agent_id="auto_agent", feedback=[_feedback()]))
    session = engine.get_session(result.session.session_id)
    assert session.status == "completed"


@pytest.mark.asyncio
async def test_session_not_found(engine: LearningEngine):
    with pytest.raises(SessionNotFoundError):
        engine.get_session("missing")


@pytest.mark.asyncio
async def test_learning_events(engine: LearningEngine):
    events: list[str] = []

    async def capture(e):
        events.append(type(e).__name__)

    subscribe(LearningCycleStartedEvent, capture)
    subscribe(LearningCycleCompletedEvent, capture)
    subscribe(FeedbackReceivedEvent, capture)

    await engine.collect_feedback(_feedback())
    await engine.learn(LearningContext(agent_id="auto_agent", feedback=[_feedback(workflow_id="wf_evt")]))
    await asyncio.sleep(0.05)

    assert "LearningCycleStartedEvent" in events
    assert "LearningCycleCompletedEvent" in events


@pytest.mark.asyncio
async def test_system_event_feedback(engine: LearningEngine):
    from platform_learning.feedback_collector import feedback_collector

    event = LearningEvent(event_type="workflow_completed", source=FeedbackSource.SYSTEM_EVENT, agent_id="auto_agent")
    fb = feedback_collector.collect_system_event(event)
    assert fb.sentiment == FeedbackSentiment.POSITIVE


@pytest.mark.asyncio
async def test_tool_execution_feedback(engine: LearningEngine):
    from platform_learning.feedback_collector import feedback_collector

    fb = feedback_collector.collect_tool_execution("crm_lookup", success=True, agent_id="auto_agent")
    assert fb.category == FeedbackCategory.TOOL


@pytest.mark.asyncio
async def test_integrations_feedback_from_decision():
    from platform_learning.integrations import learning_integrations

    fb = learning_integrations.feedback_from_decision({"decision_id": "d1", "success": True, "confidence": 88.0})
    assert fb.category == FeedbackCategory.DECISION


@pytest.mark.asyncio
async def test_integrations_orchestrator_insights():
    from platform_learning.integrations import learning_integrations

    insights = learning_integrations.orchestrator_insights({
        "session": {"session_id": "s1"},
        "recommendations": [{"id": "r1"}],
        "failure_patterns": [{}],
        "insights": {"feedback_volume": 5},
    })
    assert insights["session_id"] == "s1"


@pytest.mark.asyncio
async def test_execution_history_ingestion(engine: LearningEngine):
    ctx = LearningContext(
        agent_id="auto_agent",
        execution_history={
            "workflows": [{"workflow_id": "w1", "success": True}],
            "decisions": [{"decision_id": "d1", "success": True}],
            "planning": [{"plan_id": "p1", "success": True}],
            "reasoning": [{"session_id": "r1", "success": True}],
            "tools": [{"tool_id": "t1", "success": True}],
        },
    )
    result = await engine.learn(ctx)
    assert result.insights["experience_entries"] >= 5


@pytest.mark.asyncio
async def test_to_dict_machine_readable(engine: LearningEngine):
    result = await engine.learn(LearningContext(agent_id="auto_agent", feedback=[_feedback(), _feedback(workflow_id="wf_b")]))
    d = result.to_dict()
    assert d["session"]["session_id"]
    assert "insights" in d


@pytest.mark.asyncio
async def test_invalid_feedback_confidence():
    from platform_learning.feedback_collector import FeedbackCollector

    collector = FeedbackCollector()
    with pytest.raises(FeedbackValidationError):
        collector.collect(FeedbackRecord(confidence_score=150.0))
