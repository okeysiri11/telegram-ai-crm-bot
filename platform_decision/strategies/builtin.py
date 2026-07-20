# Decision strategies — evaluate and rank candidates.

from __future__ import annotations

from abc import ABC, abstractmethod

from platform_decision.models import DecisionCandidate, DecisionContext, DecisionCriteria, DecisionScore, DecisionStrategyType
from platform_decision.policies import DecisionPolicy


def _normalize_cost(cost: float, max_cost: float = 100.0) -> float:
    return max(0.0, 100.0 - min(cost / max_cost, 1.0) * 100.0)


def _normalize_duration(ms: float, max_ms: float = 60000.0) -> float:
    return max(0.0, 100.0 - min(ms / max_ms, 1.0) * 100.0)


def _normalize_risk(risk: float) -> float:
    return max(0.0, 100.0 - risk)


def _score_dimensions(criteria: DecisionCriteria) -> dict[str, float]:
    return {
        "execution_cost": _normalize_cost(criteria.execution_cost),
        "estimated_duration_ms": _normalize_duration(criteria.estimated_duration_ms),
        "risk_level": _normalize_risk(criteria.risk_level),
        "confidence_score": min(criteria.confidence_score, 100.0),
        "tool_availability": min(criteria.tool_availability, 100.0),
        "agent_availability": min(criteria.agent_availability, 100.0),
        "resource_consumption": max(0.0, 100.0 - criteria.resource_consumption),
        "business_priority": min(criteria.business_priority, 100.0),
        "user_preference": min(criteria.user_preference, 100.0),
    }


class BaseDecisionStrategy(ABC):
    strategy_id: DecisionStrategyType

    @abstractmethod
    def score(self, candidates: list[DecisionCandidate], context: DecisionContext, policy: DecisionPolicy) -> list[DecisionScore]: ...


class WeightedScoringStrategy(BaseDecisionStrategy):
    strategy_id = DecisionStrategyType.WEIGHTED_SCORING

    def score(self, candidates, context, policy) -> list[DecisionScore]:
        scores: list[DecisionScore] = []
        for c in candidates:
            dims = _score_dimensions(c.criteria)
            total = sum(dims[k] * policy.get_weight(k) for k in dims)
            scores.append(DecisionScore(candidate_id=c.candidate_id, total_score=round(total, 2), dimension_scores=dims))
        return sorted(scores, key=lambda s: s.total_score, reverse=True)


class RuleBasedStrategy(BaseDecisionStrategy):
    strategy_id = DecisionStrategyType.RULE_BASED

    def score(self, candidates, context, policy) -> list[DecisionScore]:
        scores: list[DecisionScore] = []
        for c in candidates:
            total = 50.0
            if c.capability and context.reasoning_result.get("intent") == c.capability:
                total += 30.0
            if c.agent_id and c.agent_id in context.available_agents:
                total += 20.0
            for rule in policy.business_rules:
                if rule in context.constraints:
                    total -= 10.0
            scores.append(DecisionScore(candidate_id=c.candidate_id, total_score=total))
        return sorted(scores, key=lambda s: s.total_score, reverse=True)


class CostOptimizationStrategy(WeightedScoringStrategy):
    strategy_id = DecisionStrategyType.COST_OPTIMIZATION

    def score(self, candidates, context, policy) -> list[DecisionScore]:
        from platform_decision.policies import policy_registry
        cost_policy = policy_registry.get("cost_first")
        return super().score(candidates, context, cost_policy)


class TimeOptimizationStrategy(WeightedScoringStrategy):
    strategy_id = DecisionStrategyType.TIME_OPTIMIZATION

    def score(self, candidates, context, policy) -> list[DecisionScore]:
        from platform_decision.policies import policy_registry
        return super().score(candidates, context, policy_registry.get("speed_first"))


class RiskAwareStrategy(WeightedScoringStrategy):
    strategy_id = DecisionStrategyType.RISK_AWARE

    def score(self, candidates, context, policy) -> list[DecisionScore]:
        from platform_decision.policies import policy_registry
        return super().score(candidates, context, policy_registry.get("risk_averse"))


class ConfidenceAwareStrategy(BaseDecisionStrategy):
    strategy_id = DecisionStrategyType.CONFIDENCE_AWARE

    def score(self, candidates, context, policy) -> list[DecisionScore]:
        reasoning_conf = context.reasoning_result.get("confidence", {}).get("overall", 50.0)
        scores: list[DecisionScore] = []
        for c in candidates:
            combined = (c.criteria.confidence_score + reasoning_conf) / 2
            scores.append(DecisionScore(
                candidate_id=c.candidate_id,
                total_score=round(combined, 2),
                dimension_scores={"confidence_score": combined},
            ))
        return sorted(scores, key=lambda s: s.total_score, reverse=True)


class MultiCriteriaStrategy(WeightedScoringStrategy):
    strategy_id = DecisionStrategyType.MULTI_CRITERIA


class FallbackStrategy(BaseDecisionStrategy):
    strategy_id = DecisionStrategyType.FALLBACK

    def score(self, candidates, context, policy) -> list[DecisionScore]:
        scores = []
        for i, c in enumerate(candidates):
            scores.append(DecisionScore(candidate_id=c.candidate_id, total_score=100.0 - i * 10))
        return scores


STRATEGY_REGISTRY: dict[str, BaseDecisionStrategy] = {
    "rule_based": RuleBasedStrategy(),
    "weighted_scoring": WeightedScoringStrategy(),
    "cost_optimization": CostOptimizationStrategy(),
    "risk_aware": RiskAwareStrategy(),
    "time_optimization": TimeOptimizationStrategy(),
    "confidence_aware": ConfidenceAwareStrategy(),
    "multi_criteria": MultiCriteriaStrategy(),
    "fallback": FallbackStrategy(),
}
