# Reasoning domain models.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ReasoningStrategy(str, Enum):
    RULE_BASED = "rule_based"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHT = "tree_of_thought"
    REFLECTIVE = "reflective"
    PLANNING_FIRST = "planning_first"
    FAST_HEURISTIC = "fast_heuristic"


@dataclass
class ConfidenceScores:
    """Multi-dimensional confidence model (0–100%)."""

    reasoning: float = 0.0
    data: float = 0.0
    memory: float = 0.0
    tool: float = 0.0

    @property
    def overall(self) -> float:
        weights = (0.35, 0.25, 0.20, 0.20)
        values = (self.reasoning, self.data, self.memory, self.tool)
        return round(sum(w * v for w, v in zip(weights, values)), 2)

    def to_dict(self) -> dict[str, float]:
        return {
            "reasoning": self.reasoning,
            "data": self.data,
            "memory": self.memory,
            "tool": self.tool,
            "overall": self.overall,
        }


@dataclass
class ReasoningStep:
    step_id: str
    phase: str
    description: str
    input_summary: str = ""
    output_summary: str = ""
    confidence: float = 0.0
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "phase": self.phase,
            "description": self.description,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "confidence": self.confidence,
            "duration_ms": self.duration_ms,
            "metadata": dict(self.metadata),
        }


@dataclass
class ReasoningTrace:
    """Machine-readable reasoning trace."""

    session_id: str
    steps: list[ReasoningStep] = field(default_factory=list)
    strategy: str = ""
    depth: int = 0
    debug: dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: ReasoningStep) -> None:
        self.steps.append(step)
        self.depth = len(self.steps)

    def human_readable(self) -> str:
        lines = [f"Reasoning trace ({self.strategy}, {len(self.steps)} steps):"]
        for i, step in enumerate(self.steps, 1):
            lines.append(f"  {i}. [{step.phase}] {step.description}")
            if step.output_summary:
                lines.append(f"     → {step.output_summary}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "strategy": self.strategy,
            "depth": self.depth,
            "steps": [s.to_dict() for s in self.steps],
            "debug": dict(self.debug),
        }


@dataclass
class ReasoningContext:
    """Input context for reasoning — integrates platform layers via metadata."""

    request: str
    agent_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    capabilities: list[str] = field(default_factory=list)
    available_tools: list[str] = field(default_factory=list)
    memory_context: dict[str, Any] = field(default_factory=dict)
    workflow_context: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "request": self.request,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "capabilities": list(self.capabilities),
            "available_tools": list(self.available_tools),
            "memory_context": dict(self.memory_context),
            "workflow_context": dict(self.workflow_context),
            "constraints": list(self.constraints),
            "metadata": dict(self.metadata),
        }


@dataclass
class ReasoningResult:
    session_id: str
    intent: str
    plan: list[str]
    constraints: list[str]
    missing_information: list[str]
    confidence: ConfidenceScores
    trace: ReasoningTrace
    strategy: ReasoningStrategy
    success: bool = True
    error: str | None = None
    execution_time_ms: float = 0.0
    recommended_capability: str | None = None
    recommended_tools: list[str] = field(default_factory=list)

    def explanation(self) -> str:
        lines = [
            f"Intent: {self.intent}",
            f"Strategy: {self.strategy.value}",
            f"Confidence: {self.confidence.overall}%",
            f"Plan: {' → '.join(self.plan) if self.plan else '(none)'}",
        ]
        if self.missing_information:
            lines.append(f"Missing: {', '.join(self.missing_information)}")
        lines.append("")
        lines.append(self.trace.human_readable())
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "intent": self.intent,
            "plan": list(self.plan),
            "constraints": list(self.constraints),
            "missing_information": list(self.missing_information),
            "confidence": self.confidence.to_dict(),
            "trace": self.trace.to_dict(),
            "strategy": self.strategy.value,
            "success": self.success,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "recommended_capability": self.recommended_capability,
            "recommended_tools": list(self.recommended_tools),
        }


@dataclass
class ReasoningSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context: ReasoningContext | None = None
    result: ReasoningResult | None = None
    strategy: ReasoningStrategy = ReasoningStrategy.FAST_HEURISTIC
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None
