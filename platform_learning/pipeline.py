# Learning pipeline — collect, analyze, recommend, store.

from __future__ import annotations

import time

from platform_learning.experience_store import ExperienceStore, experience_store
from platform_learning.feedback_collector import FeedbackCollector, feedback_collector
from platform_learning.models import LearningContext, LearningRecord, LearningResult, LearningSession
from platform_learning.pattern_analyzer import PatternAnalyzer, pattern_analyzer
from platform_learning.recommendation_engine import RecommendationEngine, recommendation_engine


class LearningPipeline:
    def __init__(
        self,
        *,
        collector: FeedbackCollector | None = None,
        store: ExperienceStore | None = None,
        analyzer: PatternAnalyzer | None = None,
        recommender: RecommendationEngine | None = None,
    ) -> None:
        self._collector = collector or feedback_collector
        self._store = store or experience_store
        self._analyzer = analyzer or pattern_analyzer
        self._recommender = recommender or recommendation_engine

    async def run(self, context: LearningContext) -> LearningResult:
        started = time.monotonic()
        session = LearningSession(
            session_id=context.session_id or LearningSession().session_id,
            agent_id=context.agent_id,
            user_id=context.user_id,
        )

        # Collect execution history into store
        history = context.execution_history
        self._ingest_history(context.agent_id, history)

        # Collect feedback
        all_feedback = list(self._collector.feedback) + list(context.feedback)
        for fb in context.feedback:
            self._collector.collect(fb)
        for event in context.events:
            self._collector.collect_system_event(event)
        all_feedback = list({f.feedback_id: f for f in all_feedback + self._collector.feedback}.values())
        session.feedback_count = len(all_feedback)

        # Analyze outcomes & detect patterns
        success_patterns, failure_patterns = self._analyzer.analyze(all_feedback)

        # Generate recommendations
        recommendations = self._recommender.generate(
            success_patterns=success_patterns,
            failure_patterns=failure_patterns,
            feedback=all_feedback,
        )

        # Store learning records
        records: list[LearningRecord] = []
        for p in success_patterns:
            records.append(LearningRecord(
                session_id=session.session_id,
                agent_id=context.agent_id,
                category=p.get("category", "general"),
                outcome="success",
                pattern_type="success_pattern",
                summary=p.get("description", ""),
                data=p,
            ))
        for p in failure_patterns:
            records.append(LearningRecord(
                session_id=session.session_id,
                agent_id=context.agent_id,
                category=p.get("category", "general"),
                outcome="failure",
                pattern_type="failure_pattern",
                summary=p.get("description", ""),
                data=p,
            ))

        session.records = records
        session.recommendations = recommendations
        session.cycle_time_ms = round((time.monotonic() - started) * 1000, 2)
        session.status = "completed"
        session.completed_at = time.time()

        insights = {
            "feedback_volume": len(all_feedback),
            "success_patterns": len(success_patterns),
            "failure_patterns": len(failure_patterns),
            "recommendations": len(recommendations),
            "experience_entries": self._store.count(),
            "pattern_detection_rate": self._analyzer.detection_rate(all_feedback),
        }
        session.insights = insights

        return LearningResult(
            session=session,
            records=records,
            recommendations=recommendations,
            success_patterns=success_patterns,
            failure_patterns=failure_patterns,
            insights=insights,
        )

    def _ingest_history(self, agent_id: str | None, history: dict) -> None:
        for wf in history.get("workflows", []):
            self._store.record_workflow(
                success=wf.get("success", True),
                agent_id=agent_id,
                data=wf,
            )
        for d in history.get("decisions", []):
            self._store.record_decision(agent_id, d)
        for p in history.get("planning", []):
            self._store.record_planning(agent_id, p)
        for r in history.get("reasoning", []):
            self._store.record_reasoning(agent_id, r)
        for t in history.get("tools", []):
            self._store.record_tool(agent_id, t)
        for t in history.get("tasks", []):
            self._store.record_task(agent_id, t)


learning_pipeline = LearningPipeline()
