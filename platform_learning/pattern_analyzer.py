# PatternAnalyzer — detect success and failure patterns.

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from platform_learning.config import DEFAULT_LEARNING_CONFIG, LearningEngineConfig
from platform_learning.experience_store import ExperienceStore, experience_store
from platform_learning.models import FeedbackRecord, FeedbackSentiment


class PatternAnalyzer:
    def __init__(
        self,
        *,
        store: ExperienceStore | None = None,
        config: LearningEngineConfig | None = None,
    ) -> None:
        self._store = store or experience_store
        self._config = config or DEFAULT_LEARNING_CONFIG

    def analyze(
        self,
        feedback: list[FeedbackRecord],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        success_patterns = self._detect_success_patterns(feedback)
        failure_patterns = self._detect_failure_patterns(feedback)
        return success_patterns, failure_patterns

    def _detect_success_patterns(self, feedback: list[FeedbackRecord]) -> list[dict[str, Any]]:
        patterns: list[dict[str, Any]] = []
        positive = [f for f in feedback if f.sentiment == FeedbackSentiment.POSITIVE]

        by_category = Counter(f.category.value for f in positive)
        for cat, count in by_category.items():
            if count >= self._config.min_pattern_occurrences:
                patterns.append({
                    "pattern_id": f"success_{cat}",
                    "type": "success_pattern",
                    "category": cat,
                    "occurrences": count,
                    "description": f"Repeated successful {cat} outcomes",
                })

        by_tool: Counter[str] = Counter()
        for f in positive:
            if f.tool_id:
                by_tool[f.tool_id] += 1
        for tool_id, count in by_tool.items():
            if count >= self._config.min_pattern_occurrences:
                patterns.append({
                    "pattern_id": f"success_tool_{tool_id}",
                    "type": "success_pattern",
                    "category": "tool",
                    "target": tool_id,
                    "occurrences": count,
                    "description": f"Tool {tool_id} consistently succeeds",
                })

        snapshot = self._store.snapshot()
        if len(snapshot["workflows_success"]) >= self._config.min_pattern_occurrences:
            patterns.append({
                "pattern_id": "success_workflow_execution",
                "type": "success_pattern",
                "category": "workflow",
                "occurrences": len(snapshot["workflows_success"]),
                "description": "Successful workflow executions detected",
            })

        return patterns

    def _detect_failure_patterns(self, feedback: list[FeedbackRecord]) -> list[dict[str, Any]]:
        patterns: list[dict[str, Any]] = []
        negative = [f for f in feedback if f.sentiment == FeedbackSentiment.NEGATIVE]

        by_category = Counter(f.category.value for f in negative)
        for cat, count in by_category.items():
            if count >= self._config.min_pattern_occurrences:
                patterns.append({
                    "pattern_id": f"failure_{cat}",
                    "type": "failure_pattern",
                    "category": cat,
                    "occurrences": count,
                    "description": f"Repeated {cat} failures",
                })

        error_messages: Counter[str] = Counter()
        for f in negative:
            key = f.message[:80] if f.message else "unknown"
            error_messages[key] += 1
        for msg, count in error_messages.items():
            if count >= self._config.failure_repeat_threshold:
                patterns.append({
                    "pattern_id": f"repeated_failure_{hash(msg) % 10000}",
                    "type": "failure_pattern",
                    "category": "repeated_failure",
                    "occurrences": count,
                    "description": f"Repeated failure: {msg}",
                    "message": msg,
                })

        by_agent: defaultdict[str, int] = defaultdict(int)
        for f in negative:
            if f.agent_id:
                by_agent[f.agent_id] += 1
        for agent_id, count in by_agent.items():
            if count >= self._config.min_pattern_occurrences:
                patterns.append({
                    "pattern_id": f"failure_agent_{agent_id}",
                    "type": "failure_pattern",
                    "category": "agent",
                    "target": agent_id,
                    "occurrences": count,
                    "description": f"Agent {agent_id} has recurring failures",
                })

        return patterns

    def detection_rate(self, feedback: list[FeedbackRecord]) -> float:
        if not feedback:
            return 0.0
        success, failure = self.analyze(feedback)
        detected = len(success) + len(failure)
        return round(min(detected / max(len(feedback), 1), 1.0) * 100, 2)


pattern_analyzer = PatternAnalyzer()
