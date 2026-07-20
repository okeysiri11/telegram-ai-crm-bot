# FeedbackCollector — ingest feedback from multiple sources.

from __future__ import annotations

import logging

from platform_learning.exceptions import FeedbackValidationError
from platform_learning.experience_store import ExperienceStore, experience_store
from platform_learning.models import (
    FeedbackCategory,
    FeedbackRecord,
    FeedbackSentiment,
    FeedbackSource,
    LearningEvent,
)

logger = logging.getLogger(__name__)


class FeedbackCollector:
    def __init__(self, *, store: ExperienceStore | None = None) -> None:
        self._store = store or experience_store
        self._feedback: list[FeedbackRecord] = []

    def reset(self) -> None:
        self._feedback.clear()

    @property
    def feedback(self) -> list[FeedbackRecord]:
        return list(self._feedback)

    def collect(self, record: FeedbackRecord) -> FeedbackRecord:
        errors = self._validate(record)
        if errors:
            raise FeedbackValidationError("Invalid feedback record", details=errors)
        self._feedback.append(record)
        self._route_to_store(record)
        logger.debug("feedback_collected id=%s source=%s", record.feedback_id, record.source.value)
        return record

    def collect_workflow_result(
        self,
        workflow_id: str,
        *,
        success: bool,
        agent_id: str | None = None,
        message: str = "",
    ) -> FeedbackRecord:
        record = FeedbackRecord(
            sentiment=FeedbackSentiment.POSITIVE if success else FeedbackSentiment.NEGATIVE,
            confidence_score=90.0 if success else 80.0,
            severity=0.0 if success else 60.0,
            priority=70.0,
            category=FeedbackCategory.WORKFLOW,
            source=FeedbackSource.WORKFLOW_RESULT,
            message=message or f"Workflow {'completed' if success else 'failed'}",
            agent_id=agent_id,
            workflow_id=workflow_id,
        )
        return self.collect(record)

    def collect_task_result(
        self,
        task_id: str,
        *,
        success: bool,
        agent_id: str | None = None,
    ) -> FeedbackRecord:
        return self.collect(
            FeedbackRecord(
                sentiment=FeedbackSentiment.POSITIVE if success else FeedbackSentiment.NEGATIVE,
                confidence_score=85.0,
                category=FeedbackCategory.GENERAL,
                source=FeedbackSource.TASK_RESULT,
                message=f"Task {'completed' if success else 'failed'}",
                agent_id=agent_id,
                task_id=task_id,
            )
        )

    def collect_human_feedback(
        self,
        message: str,
        *,
        sentiment: FeedbackSentiment = FeedbackSentiment.NEUTRAL,
        agent_id: str | None = None,
        category: FeedbackCategory = FeedbackCategory.GENERAL,
        priority: float = 80.0,
    ) -> FeedbackRecord:
        return self.collect(
            FeedbackRecord(
                sentiment=sentiment,
                confidence_score=95.0,
                priority=priority,
                category=category,
                source=FeedbackSource.HUMAN_FEEDBACK,
                message=message,
                agent_id=agent_id,
            )
        )

    def collect_agent_self_eval(
        self,
        agent_id: str,
        message: str,
        *,
        sentiment: FeedbackSentiment = FeedbackSentiment.NEUTRAL,
        confidence_score: float = 70.0,
    ) -> FeedbackRecord:
        return self.collect(
            FeedbackRecord(
                sentiment=sentiment,
                confidence_score=confidence_score,
                category=FeedbackCategory.AGENT,
                source=FeedbackSource.AGENT_SELF_EVAL,
                message=message,
                agent_id=agent_id,
            )
        )

    def collect_tool_execution(
        self,
        tool_id: str,
        *,
        success: bool,
        agent_id: str | None = None,
        message: str = "",
    ) -> FeedbackRecord:
        return self.collect(
            FeedbackRecord(
                sentiment=FeedbackSentiment.POSITIVE if success else FeedbackSentiment.NEGATIVE,
                confidence_score=88.0,
                severity=10.0 if success else 50.0,
                category=FeedbackCategory.TOOL,
                source=FeedbackSource.TOOL_EXECUTION,
                message=message or f"Tool {tool_id} {'succeeded' if success else 'failed'}",
                agent_id=agent_id,
                tool_id=tool_id,
            )
        )

    def collect_system_event(self, event: LearningEvent) -> FeedbackRecord:
        sentiment = FeedbackSentiment.NEUTRAL
        if event.event_type.endswith("_failed"):
            sentiment = FeedbackSentiment.NEGATIVE
        elif event.event_type.endswith("_completed"):
            sentiment = FeedbackSentiment.POSITIVE
        return self.collect(
            FeedbackRecord(
                sentiment=sentiment,
                confidence_score=75.0,
                category=FeedbackCategory.GENERAL,
                source=FeedbackSource.SYSTEM_EVENT,
                message=event.event_type,
                agent_id=event.agent_id,
                metadata=dict(event.payload),
            )
        )

    def collect_error_report(
        self,
        message: str,
        *,
        agent_id: str | None = None,
        severity: float = 80.0,
        category: FeedbackCategory = FeedbackCategory.GENERAL,
    ) -> FeedbackRecord:
        return self.collect(
            FeedbackRecord(
                sentiment=FeedbackSentiment.NEGATIVE,
                confidence_score=90.0,
                severity=severity,
                priority=90.0,
                category=category,
                source=FeedbackSource.ERROR_REPORT,
                message=message,
                agent_id=agent_id,
            )
        )

    def _validate(self, record: FeedbackRecord) -> list[str]:
        errors: list[str] = []
        if not record.feedback_id:
            errors.append("missing_feedback_id")
        if record.confidence_score < 0 or record.confidence_score > 100:
            errors.append("invalid_confidence_score")
        return errors

    def _route_to_store(self, record: FeedbackRecord) -> None:
        data = record.to_dict()
        if record.workflow_id:
            self._store.record_workflow(
                success=record.sentiment == FeedbackSentiment.POSITIVE,
                agent_id=record.agent_id,
                data={**data, "workflow_id": record.workflow_id},
            )
        if record.task_id:
            self._store.record_task(record.agent_id, {**data, "task_id": record.task_id, "success": record.sentiment == FeedbackSentiment.POSITIVE})
        if record.tool_id:
            self._store.record_tool(record.agent_id, {**data, "tool_id": record.tool_id, "success": record.sentiment == FeedbackSentiment.POSITIVE})
        if record.category == FeedbackCategory.AGENT and record.agent_id:
            self._store.record_agent_performance(
                record.agent_id,
                {"outcome": "success" if record.sentiment == FeedbackSentiment.POSITIVE else "failure", **data},
            )


feedback_collector = FeedbackCollector()
