# Confidence estimation model.

from __future__ import annotations

from platform_reasoning.models import ConfidenceScores, ReasoningContext, ReasoningTrace


class ConfidenceEstimator:
    """Estimate multi-dimensional confidence scores (0–100%)."""

    def estimate(
        self,
        context: ReasoningContext,
        strategy_data: dict,
        trace: ReasoningTrace,
    ) -> ConfidenceScores:
        reasoning_conf = self._reasoning_confidence(trace, strategy_data)
        data_conf = self._data_confidence(context)
        memory_conf = self._memory_confidence(context)
        tool_conf = self._tool_confidence(context, strategy_data)

        return ConfidenceScores(
            reasoning=reasoning_conf,
            data=data_conf,
            memory=memory_conf,
            tool=tool_conf,
        )

    def _reasoning_confidence(self, trace: ReasoningTrace, data: dict) -> float:
        if not trace.steps:
            return 30.0
        step_confidences = [s.confidence for s in trace.steps if s.confidence > 0]
        base = sum(step_confidences) / len(step_confidences) if step_confidences else 50.0
        boost = data.get("confidence_boost", 0)
        depth_bonus = min(len(trace.steps) * 2, 15)
        return min(round(base + boost + depth_bonus, 2), 100.0)

    def _data_confidence(self, context: ReasoningContext) -> float:
        score = 40.0
        if len(context.request) > 20:
            score += 15
        if context.constraints:
            score += 10
        if context.user_id:
            score += 10
        if context.capabilities:
            score += 10
        return min(score, 100.0)

    def _memory_confidence(self, context: ReasoningContext) -> float:
        if not context.memory_context:
            return 30.0
        facts = context.memory_context.get("facts", [])
        return min(40 + len(facts) * 10, 95.0)

    def _tool_confidence(self, context: ReasoningContext, data: dict) -> float:
        if not context.available_tools:
            return 40.0
        intent = data.get("intent", "")
        matching = sum(1 for t in context.available_tools if intent.split("_")[0] in t)
        return min(50 + matching * 15, 95.0)
