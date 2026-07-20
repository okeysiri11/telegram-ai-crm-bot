# Reasoning strategy base class.

from __future__ import annotations

from abc import ABC, abstractmethod

from platform_reasoning.models import ReasoningContext, ReasoningStep, ReasoningTrace


class BaseReasoningStrategy(ABC):
    """Abstract reasoning strategy — no LLM dependency."""

    strategy_id: str = ""

    @abstractmethod
    async def reason(self, context: ReasoningContext, trace: ReasoningTrace) -> dict:
        """Execute strategy and return intermediate reasoning data."""

    def _step(
        self,
        trace: ReasoningTrace,
        phase: str,
        description: str,
        *,
        input_summary: str = "",
        output_summary: str = "",
        confidence: float = 0.0,
        duration_ms: float = 0.0,
    ) -> ReasoningStep:
        import uuid

        step = ReasoningStep(
            step_id=str(uuid.uuid4()),
            phase=phase,
            description=description,
            input_summary=input_summary,
            output_summary=output_summary,
            confidence=confidence,
            duration_ms=duration_ms,
        )
        trace.add_step(step)
        return step
