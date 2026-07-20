# Learning domain models.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FeedbackSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class FeedbackSource(str, Enum):
    WORKFLOW_RESULT = "workflow_result"
    TASK_RESULT = "task_result"
    HUMAN_FEEDBACK = "human_feedback"
    AGENT_SELF_EVAL = "agent_self_evaluation"
    TOOL_EXECUTION = "tool_execution"
    SYSTEM_EVENT = "system_event"
    ERROR_REPORT = "error_report"


class FeedbackCategory(str, Enum):
    WORKFLOW = "workflow"
    PLANNING = "planning"
    DECISION = "decision"
    REASONING = "reasoning"
    TOOL = "tool"
    AGENT = "agent"
    GENERAL = "general"


class RecommendationType(str, Enum):
    PLANNING_STRATEGY = "planning_strategy"
    DECISION_POLICY = "decision_policy"
    TOOL = "tool"
    AGENT = "agent"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    REPEATED_FAILURE = "repeated_failure"


@dataclass
class FeedbackRecord:
    feedback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sentiment: FeedbackSentiment = FeedbackSentiment.NEUTRAL
    confidence_score: float = 50.0
    severity: float = 0.0  # 0=low, 100=high
    priority: float = 50.0
    category: FeedbackCategory = FeedbackCategory.GENERAL
    source: FeedbackSource = FeedbackSource.SYSTEM_EVENT
    message: str = ""
    agent_id: str | None = None
    workflow_id: str | None = None
    task_id: str | None = None
    tool_id: str | None = None
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "sentiment": self.sentiment.value,
            "confidence_score": self.confidence_score,
            "severity": self.severity,
            "priority": self.priority,
            "category": self.category.value,
            "source": self.source.value,
            "message": self.message,
            "agent_id": self.agent_id,
            "workflow_id": self.workflow_id,
            "timestamp": self.timestamp,
        }


@dataclass
class LearningRecord:
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    agent_id: str | None = None
    category: str = "general"
    outcome: str = "unknown"  # success | failure | partial
    pattern_type: str | None = None  # success_pattern | failure_pattern
    summary: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "category": self.category,
            "outcome": self.outcome,
            "pattern_type": self.pattern_type,
            "summary": self.summary,
            "timestamp": self.timestamp,
        }


@dataclass
class LearningEvent:
    """Domain learning event (distinct from platform event bus)."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    source: FeedbackSource = FeedbackSource.SYSTEM_EVENT
    agent_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source.value,
            "agent_id": self.agent_id,
            "payload": dict(self.payload),
            "timestamp": self.timestamp,
        }


@dataclass
class Recommendation:
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recommendation_type: RecommendationType = RecommendationType.WORKFLOW_OPTIMIZATION
    title: str = ""
    description: str = ""
    target: str = ""
    suggested_value: str = ""
    confidence: float = 50.0
    priority: float = 50.0
    evidence: list[str] = field(default_factory=list)
    accepted: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "recommendation_type": self.recommendation_type.value,
            "title": self.title,
            "description": self.description,
            "target": self.target,
            "suggested_value": self.suggested_value,
            "confidence": self.confidence,
            "priority": self.priority,
            "evidence": list(self.evidence),
            "accepted": self.accepted,
        }


@dataclass
class LearningContext:
    agent_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    feedback: list[FeedbackRecord] = field(default_factory=list)
    events: list[LearningEvent] = field(default_factory=list)
    execution_history: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str | None = None
    user_id: str | None = None
    status: str = "active"  # active | completed | failed
    feedback_count: int = 0
    records: list[LearningRecord] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    insights: dict[str, Any] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    cycle_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "status": self.status,
            "feedback_count": self.feedback_count,
            "records_count": len(self.records),
            "recommendations_count": len(self.recommendations),
            "insights": dict(self.insights),
            "cycle_time_ms": self.cycle_time_ms,
        }


@dataclass
class LearningResult:
    session: LearningSession
    records: list[LearningRecord] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    success_patterns: list[dict[str, Any]] = field(default_factory=list)
    failure_patterns: list[dict[str, Any]] = field(default_factory=list)
    insights: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session": self.session.to_dict(),
            "records": [r.to_dict() for r in self.records],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "success_patterns": list(self.success_patterns),
            "failure_patterns": list(self.failure_patterns),
            "insights": dict(self.insights),
            "success": self.success,
        }
