# Continuous learning — history analysis, outcomes, feedback, experience replay.

from __future__ import annotations

from typing import Any

from events.publisher import publish

from ecosystem.optimization.events import LearningCycleCompletedEvent
from ecosystem.optimization.models import DecisionOutcome, ExecutionRecord, FeedbackItem, LearningCycle
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class ContinuousLearningService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def record_execution(
        self,
        source: str,
        action: str,
        *,
        outcome: str = "success",
        duration_ms: float = 0.0,
        application_id: str = "",
        agent_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionRecord:
        record = ExecutionRecord(
            source=source,
            action=action,
            outcome=outcome,
            duration_ms=duration_ms,
            application_id=application_id,
            agent_id=agent_id,
            metadata=metadata or {},
        )
        self._store.execution_records.save(record.record_id, record)
        return record

    def track_decision(
        self,
        decision_id: str,
        decision_type: str,
        *,
        expected: str = "",
        actual: str = "",
        success: bool = True,
        score: float = 1.0,
        lessons: list[str] | None = None,
    ) -> DecisionOutcome:
        outcome = DecisionOutcome(
            decision_id=decision_id,
            decision_type=decision_type,
            expected=expected,
            actual=actual or ("ok" if success else "failed"),
            success=success,
            score=score,
            lessons=lessons or [],
        )
        self._store.decision_outcomes.save(outcome.outcome_id, outcome)
        return outcome

    def ingest_feedback(
        self,
        *,
        source: str = "user",
        target_type: str = "workflow",
        target_id: str = "",
        rating: float = 0.0,
        comment: str = "",
        tags: list[str] | None = None,
    ) -> FeedbackItem:
        item = FeedbackItem(
            source=source,
            target_type=target_type,
            target_id=target_id,
            rating=rating,
            comment=comment,
            tags=tags or [],
        )
        self._store.feedback_items.save(item.feedback_id, item)
        return item

    def analyze_history(self, *, limit: int = 200) -> dict[str, Any]:
        records = sorted(self._store.execution_records.list_all(), key=lambda r: r.created_at, reverse=True)[:limit]
        successes = [r for r in records if r.outcome == "success"]
        failures = [r for r in records if r.outcome != "success"]
        avg_latency = sum(r.duration_ms for r in records) / len(records) if records else 0.0
        by_agent: dict[str, int] = {}
        for r in records:
            key = r.agent_id or "unknown"
            by_agent[key] = by_agent.get(key, 0) + 1
        return {
            "total": len(records),
            "successes": len(successes),
            "failures": len(failures),
            "success_rate": round(len(successes) / len(records), 3) if records else 0.0,
            "avg_latency_ms": round(avg_latency, 2),
            "by_agent": by_agent,
        }

    def experience_replay(self, *, limit: int = 20) -> list[ExecutionRecord]:
        records = sorted(self._store.execution_records.list_all(), key=lambda r: r.created_at, reverse=True)[:limit]
        # Replay = re-surface historical executions for learning
        return records

    def refine_knowledge(self) -> list[dict[str, Any]]:
        outcomes = self._store.decision_outcomes.list_all()
        feedback = self._store.feedback_items.list_all()
        refinements: list[dict[str, Any]] = []
        for outcome in outcomes:
            if not outcome.success:
                refinements.append(
                    {
                        "type": "decision_refinement",
                        "decision_id": outcome.decision_id,
                        "lesson": outcome.lessons[0] if outcome.lessons else "Review failed decision path",
                    }
                )
        low_ratings = [f for f in feedback if f.rating < 3.0]
        for item in low_ratings:
            refinements.append(
                {
                    "type": "feedback_refinement",
                    "target_id": item.target_id,
                    "lesson": item.comment or "Improve based on low rating",
                }
            )
        return refinements

    async def run_learning_cycle(self) -> LearningCycle:
        analysis = self.analyze_history()
        refinements = self.refine_knowledge()
        replayed = self.experience_replay()
        insights = []
        if analysis["success_rate"] < 0.9:
            insights.append("Success rate below 90% — prioritize failure pattern analysis")
        if analysis["avg_latency_ms"] > 500:
            insights.append("Average latency elevated — consider workflow optimization")
        if refinements:
            insights.append(f"{len(refinements)} knowledge refinements identified")
        if not insights:
            insights.append("Ecosystem performance within healthy bounds")

        # Integrate with global knowledge / assistant memory when available
        try:
            from ecosystem.assistant.knowledge_graph.service import knowledge_graph

            await knowledge_graph.upsert_node(
                "Learning Cycle Insight",
                "; ".join(insights),
                node_type="learning",
                application_id="ecosystem",
                tags=["optimization", "learning"],
            )
        except Exception:
            pass

        cycle = LearningCycle(
            records_analyzed=analysis["total"],
            insights=insights,
            refinements=refinements,
            replayed=len(replayed),
        )
        self._store.learning_cycles.save(cycle.cycle_id, cycle)
        await publish(
            LearningCycleCompletedEvent(
                cycle_id=cycle.cycle_id,
                records_analyzed=cycle.records_analyzed,
                insights=list(insights),
            )
        )
        return cycle

    def list_cycles(self) -> list[LearningCycle]:
        return sorted(self._store.learning_cycles.list_all(), key=lambda c: c.created_at, reverse=True)


continuous_learning = ContinuousLearningService()
