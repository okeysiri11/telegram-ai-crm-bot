# Reasoning pipeline — understand, plan, estimate confidence, produce result.

from __future__ import annotations

import time
import uuid

from platform_reasoning.confidence import ConfidenceEstimator
from platform_reasoning.exceptions import ReasoningPipelineError
from platform_reasoning.models import (
    ConfidenceScores,
    ReasoningContext,
    ReasoningResult,
    ReasoningSession,
    ReasoningStrategy,
    ReasoningTrace,
)
from platform_reasoning.strategies.builtin import STRATEGY_REGISTRY


class ReasoningPipeline:
    """Standard reasoning pipeline executed before workflow/agent actions."""

    def __init__(self, *, debug: bool = False) -> None:
        self._confidence = ConfidenceEstimator()
        self._debug = debug

    async def run(
        self,
        context: ReasoningContext,
        strategy: ReasoningStrategy | str = ReasoningStrategy.FAST_HEURISTIC,
    ) -> ReasoningResult:
        started = time.monotonic()
        session_id = str(uuid.uuid4())
        strategy_key = strategy.value if isinstance(strategy, ReasoningStrategy) else strategy

        if strategy_key not in STRATEGY_REGISTRY:
            raise ReasoningPipelineError("strategy", f"Unknown strategy: {strategy_key}")

        trace = ReasoningTrace(session_id=session_id, strategy=strategy_key, debug={"debug_mode": self._debug})

        # Phase 1: Understand request
        t0 = time.monotonic()
        trace.add_step(self._phase_step("understand", "Analyzing user request", context.request[:120], t0))

        # Phase 2–6: Strategy execution (intent, constraints, missing info, plan)
        strategy_impl = STRATEGY_REGISTRY[strategy_key]
        data = await strategy_impl.reason(context, trace)

        intent = data.get("intent", "general_inquiry")
        constraints = data.get("constraints", list(context.constraints))
        missing = data.get("missing_information", self._detect_missing(context, intent))
        plan = data.get("plan", self._default_plan(intent, missing))

        # Phase 7: Estimate confidence
        confidence = self._confidence.estimate(context, data, trace)

        # Phase 8: Structured result
        recommended_tools = [
            t for t in context.available_tools
            if intent.split("_")[0] in t or intent in t
        ][:3]

        result = ReasoningResult(
            session_id=session_id,
            intent=intent,
            plan=plan,
            constraints=constraints,
            missing_information=missing,
            confidence=confidence,
            trace=trace,
            strategy=ReasoningStrategy(strategy_key),
            recommended_capability=intent if intent != "general_inquiry" else None,
            recommended_tools=recommended_tools,
            execution_time_ms=round((time.monotonic() - started) * 1000, 2),
        )

        if self._debug:
            trace.debug["result"] = result.to_dict()

        return result

    def _detect_missing(self, context: ReasoningContext, intent: str) -> list[str]:
        missing: list[str] = []
        if intent == "buy_car" and "budget" not in context.request.lower():
            missing.append("budget")
        if intent == "legal_contract" and "contract" not in context.request.lower():
            missing.append("document_reference")
        if not context.user_id:
            missing.append("user_identity")
        return missing

    def _default_plan(self, intent: str, missing: list[str]) -> list[str]:
        plan = ["understand_request"]
        if missing:
            plan.append("clarify_missing_information")
        plan.extend([f"route_to_{intent}", "execute", "verify"])
        return plan

    def _phase_step(self, phase: str, description: str, input_summary: str, started: float):
        from platform_reasoning.models import ReasoningStep

        return ReasoningStep(
            step_id=str(uuid.uuid4()),
            phase=phase,
            description=description,
            input_summary=input_summary,
            confidence=50.0,
            duration_ms=round((time.monotonic() - started) * 1000, 2),
        )


reasoning_pipeline = ReasoningPipeline()
