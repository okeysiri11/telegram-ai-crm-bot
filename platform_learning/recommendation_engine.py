# RecommendationEngine — generate improvement recommendations.

from __future__ import annotations

from typing import Any

from platform_learning.config import DEFAULT_LEARNING_CONFIG, LearningEngineConfig
from platform_learning.experience_store import ExperienceStore, experience_store
from platform_learning.models import FeedbackRecord, FeedbackSentiment, Recommendation, RecommendationType


class RecommendationEngine:
    def __init__(
        self,
        *,
        store: ExperienceStore | None = None,
        config: LearningEngineConfig | None = None,
    ) -> None:
        self._store = store or experience_store
        self._config = config or DEFAULT_LEARNING_CONFIG
        self._acceptance: dict[str, bool] = {}

    def reset(self) -> None:
        self._acceptance.clear()

    def generate(
        self,
        *,
        success_patterns: list[dict[str, Any]],
        failure_patterns: list[dict[str, Any]],
        feedback: list[FeedbackRecord],
    ) -> list[Recommendation]:
        recommendations: list[Recommendation] = []

        recommendations.extend(self._planning_recommendations(success_patterns, failure_patterns))
        recommendations.extend(self._decision_recommendations(failure_patterns))
        recommendations.extend(self._tool_recommendations(success_patterns, failure_patterns, feedback))
        recommendations.extend(self._agent_recommendations(failure_patterns, feedback))
        recommendations.extend(self._workflow_recommendations(success_patterns, failure_patterns))
        recommendations.extend(self._repeated_failure_recommendations(failure_patterns))

        return recommendations[: self._config.max_recommendations]

    def accept(self, recommendation_id: str) -> None:
        self._acceptance[recommendation_id] = True

    def reject(self, recommendation_id: str) -> None:
        self._acceptance[recommendation_id] = False

    def acceptance_rate(self) -> float:
        if not self._acceptance:
            return 0.0
        accepted = sum(1 for v in self._acceptance.values() if v)
        return round(accepted / len(self._acceptance), 4)

    def _planning_recommendations(
        self,
        success: list[dict[str, Any]],
        failure: list[dict[str, Any]],
    ) -> list[Recommendation]:
        recs: list[Recommendation] = []
        planning_failures = [p for p in failure if p.get("category") == "planning"]
        if planning_failures:
            recs.append(Recommendation(
                recommendation_type=RecommendationType.PLANNING_STRATEGY,
                title="Switch planning strategy",
                description="Planning failures detected — try dependency_aware or adaptive_replanning",
                target="planning_strategy",
                suggested_value="dependency_aware",
                confidence=75.0,
                priority=80.0,
                evidence=[p["description"] for p in planning_failures],
            ))
        planning_success = [p for p in success if p.get("category") == "planning"]
        if planning_success and not planning_failures:
            recs.append(Recommendation(
                recommendation_type=RecommendationType.PLANNING_STRATEGY,
                title="Continue current planning approach",
                description="Planning outcomes are consistently successful",
                target="planning_strategy",
                suggested_value="keep_current",
                confidence=85.0,
                priority=40.0,
                evidence=[p["description"] for p in planning_success],
            ))
        return recs

    def _decision_recommendations(self, failure: list[dict[str, Any]]) -> list[Recommendation]:
        recs: list[Recommendation] = []
        decision_failures = [p for p in failure if p.get("category") == "decision"]
        if decision_failures:
            recs.append(Recommendation(
                recommendation_type=RecommendationType.DECISION_POLICY,
                title="Use risk-averse decision policy",
                description="Decision failures suggest switching to risk_averse policy",
                target="decision_policy",
                suggested_value="risk_averse",
                confidence=70.0,
                priority=75.0,
                evidence=[p["description"] for p in decision_failures],
            ))
        return recs

    def _tool_recommendations(
        self,
        success: list[dict[str, Any]],
        failure: list[dict[str, Any]],
        feedback: list[FeedbackRecord],
    ) -> list[Recommendation]:
        recs: list[Recommendation] = []
        for p in success:
            if p.get("category") == "tool" and p.get("target"):
                recs.append(Recommendation(
                    recommendation_type=RecommendationType.TOOL,
                    title=f"Prefer tool {p['target']}",
                    description=p["description"],
                    target=p["target"],
                    suggested_value="prefer",
                    confidence=80.0,
                    priority=60.0,
                    evidence=[p["description"]],
                ))
        failed_tools = {f.tool_id for f in feedback if f.tool_id and f.sentiment == FeedbackSentiment.NEGATIVE}
        for tool_id in failed_tools:
            recs.append(Recommendation(
                recommendation_type=RecommendationType.TOOL,
                title=f"Avoid or retry tool {tool_id}",
                description=f"Tool {tool_id} has failure history",
                target=tool_id,
                suggested_value="avoid_or_fallback",
                confidence=72.0,
                priority=70.0,
                evidence=[f"Tool {tool_id} failed"],
            ))
        return recs

    def _agent_recommendations(
        self,
        failure: list[dict[str, Any]],
        feedback: list[FeedbackRecord],
    ) -> list[Recommendation]:
        recs: list[Recommendation] = []
        for p in failure:
            if p.get("category") == "agent" and p.get("target"):
                recs.append(Recommendation(
                    recommendation_type=RecommendationType.AGENT,
                    title=f"Review agent {p['target']}",
                    description=p["description"],
                    target=p["target"],
                    suggested_value="review_or_reassign",
                    confidence=78.0,
                    priority=85.0,
                    evidence=[p["description"]],
                ))
        positive_agents = {f.agent_id for f in feedback if f.agent_id and f.sentiment == FeedbackSentiment.POSITIVE}
        for agent_id in positive_agents:
            recs.append(Recommendation(
                recommendation_type=RecommendationType.AGENT,
                title=f"Prefer agent {agent_id}",
                description="Agent has strong positive feedback history",
                target=agent_id,
                suggested_value="prefer",
                confidence=82.0,
                priority=55.0,
                evidence=[f"Agent {agent_id} positive feedback"],
            ))
        return recs

    def _workflow_recommendations(
        self,
        success: list[dict[str, Any]],
        failure: list[dict[str, Any]],
    ) -> list[Recommendation]:
        recs: list[Recommendation] = []
        snapshot = self._store.snapshot()
        fail_count = len(snapshot["workflows_failed"])
        success_count = len(snapshot["workflows_success"])
        if fail_count > success_count and fail_count >= self._config.min_pattern_occurrences:
            recs.append(Recommendation(
                recommendation_type=RecommendationType.WORKFLOW_OPTIMIZATION,
                title="Optimize workflow execution",
                description="More workflow failures than successes — review step dependencies",
                target="workflow",
                suggested_value="review_dependencies",
                confidence=76.0,
                priority=88.0,
                evidence=[f"{fail_count} failed vs {success_count} successful workflows"],
            ))
        elif success_count >= self._config.min_pattern_occurrences:
            recs.append(Recommendation(
                recommendation_type=RecommendationType.WORKFLOW_OPTIMIZATION,
                title="Replicate successful workflow patterns",
                description="Strong workflow success rate — template for future runs",
                target="workflow",
                suggested_value="template_success_pattern",
                confidence=84.0,
                priority=50.0,
                evidence=[f"{success_count} successful workflows"],
            ))
        return recs

    def _repeated_failure_recommendations(self, failure: list[dict[str, Any]]) -> list[Recommendation]:
        recs: list[Recommendation] = []
        for p in failure:
            if p.get("category") == "repeated_failure":
                recs.append(Recommendation(
                    recommendation_type=RecommendationType.REPEATED_FAILURE,
                    title="Address repeated failure",
                    description=p.get("description", "Repeated failure detected"),
                    target=p.get("message", "unknown"),
                    suggested_value="investigate_and_fix",
                    confidence=90.0,
                    priority=95.0,
                    evidence=[p["description"]],
                ))
        return recs


recommendation_engine = RecommendationEngine()
