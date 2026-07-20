# Decision pipeline — validate, score, rank, select, explain.

from __future__ import annotations

import time
import uuid

from platform_decision.exceptions import DecisionValidationError, NoCandidatesError
from platform_decision.models import (
    DecisionCandidate,
    DecisionContext,
    DecisionResult,
    DecisionScore,
    DecisionStrategyType,
    DecisionTrace,
)
from platform_decision.policies import DecisionPolicy, policy_registry
from platform_decision.strategies.builtin import STRATEGY_REGISTRY


class DecisionPipeline:
    async def run(
        self,
        context: DecisionContext,
        *,
        strategy: DecisionStrategyType | str = DecisionStrategyType.MULTI_CRITERIA,
        policy_id: str = "balanced",
    ) -> DecisionResult:
        started = time.monotonic()
        decision_id = str(uuid.uuid4())
        strategy_key = strategy.value if isinstance(strategy, DecisionStrategyType) else strategy

        if strategy_key not in STRATEGY_REGISTRY:
            strategy_key = "multi_criteria"

        policy = policy_registry.get(policy_id)
        trace = DecisionTrace(decision_id=decision_id, strategy=strategy_key, policy_id=policy_id)

        # Receive & validate candidates
        candidates = list(context.candidates)
        if not candidates:
            raise NoCandidatesError()

        trace.add_step("receive", f"Received {len(candidates)} candidates")
        validation_errors = self._validate_candidates(candidates, context)
        if validation_errors:
            raise DecisionValidationError("Candidate validation failed", details=validation_errors)
        trace.add_step("validate", "All candidates validated")

        # Evaluate constraints
        valid = [c for c in candidates if c.valid]
        if not valid:
            raise NoCandidatesError()
        trace.add_step("constraints", f"{len(valid)} candidates pass constraints")

        # Score & rank
        impl = STRATEGY_REGISTRY[strategy_key]
        ranked = impl.score(valid, context, policy)
        for i, score in enumerate(ranked):
            score.rank = i + 1
        trace.add_step("score", f"Scored {len(ranked)} candidates via {strategy_key}")

        # Select best
        best_id = ranked[0].candidate_id
        selected = next(c for c in valid if c.candidate_id == best_id)
        alternatives = [c for c in valid if c.candidate_id != best_id]
        trace.add_step("select", f"Selected '{selected.name}' (score={ranked[0].total_score:.1f})")

        # Confidence
        confidence = min(ranked[0].total_score, 100.0)
        if len(ranked) > 1:
            gap = ranked[0].total_score - ranked[1].total_score
            confidence = min(confidence, 50.0 + gap)

        trace.alternatives = [
            {"candidate_id": s.candidate_id, "name": next((c.name for c in valid if c.candidate_id == s.candidate_id), ""), "total_score": s.total_score}
            for s in ranked[1:6]
        ]
        trace.add_step("explain", f"Confidence={confidence:.1f}%, {len(alternatives)} alternatives retained")

        return DecisionResult(
            decision_id=decision_id,
            selected=selected,
            ranked=ranked,
            alternatives=alternatives,
            confidence=round(confidence, 2),
            trace=trace,
            strategy=DecisionStrategyType(strategy_key),
            policy_id=policy_id,
            decision_time_ms=round((time.monotonic() - started) * 1000, 2),
        )

    def _validate_candidates(self, candidates: list[DecisionCandidate], context: DecisionContext) -> list[str]:
        errors: list[str] = []
        ids = set()
        for c in candidates:
            if c.candidate_id in ids:
                errors.append(f"duplicate_candidate: {c.candidate_id}")
            ids.add(c.candidate_id)
            if not c.name:
                errors.append(f"missing_name: {c.candidate_id}")
            if c.agent_id and context.available_agents and c.agent_id not in context.available_agents:
                c.valid = False
        return errors


decision_pipeline = DecisionPipeline()
