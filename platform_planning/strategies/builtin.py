# Planning strategies.

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from platform_planning.models import PlanCandidate, PlanningContext, PlanningStrategy, PlanStep


class BasePlanningStrategy(ABC):
    strategy_id: PlanningStrategy

    @abstractmethod
    def generate(self, context: PlanningContext) -> PlanCandidate: ...


GOAL_TEMPLATES: dict[str, list[tuple[str, str, str | None]]] = {
    "buy_car": [
        ("search", "Search vehicles", "buy_car"),
        ("inspect", "Vehicle inspection", "vehicle_inspection"),
        ("finance", "Arrange financing", "auto_financing"),
    ],
    "legal_contract": [
        ("review", "Review contract", "legal_contract"),
        ("compliance", "Compliance check", "compliance_check"),
    ],
    "grain_trade": [
        ("analyze", "Crop analysis", "crop_analysis"),
        ("quote", "Freight quote", "freight_quote"),
        ("trade", "Execute trade", "grain_trade"),
    ],
    "market_analysis": [
        ("gather", "Gather data", "search_query"),
        ("analyze", "Market analysis", "market_analysis"),
        ("report", "Generate report", "inventory_report"),
    ],
    "general": [
        ("understand", "Understand goal", None),
        ("execute", "Execute primary action", None),
        ("verify", "Verify result", None),
    ],
}


def _resolve_intent(context: PlanningContext) -> str:
    if context.intent:
        return context.intent
    reasoning = context.reasoning_result.get("intent")
    if reasoning:
        return reasoning
    goal_lower = context.goal.lower()
    for intent in GOAL_TEMPLATES:
        if intent != "general" and intent.replace("_", " ") in goal_lower:
            return intent
        keywords = intent.split("_")
        if any(kw in goal_lower for kw in keywords):
            return intent
    return "general"


def _build_steps(templates: list[tuple[str, str, str | None]], *, parallel_group: str | None = None) -> list[PlanStep]:
    steps: list[PlanStep] = []
    prev_id: str | None = None
    for key, name, cap in templates:
        step_id = f"step_{key}"
        depends = [prev_id] if prev_id else []
        steps.append(
            PlanStep(
                step_id=step_id,
                name=name,
                capability=cap,
                depends_on=depends,
                parallel_group=parallel_group,
                estimated_cost=1.0,
            )
        )
        if not parallel_group:
            prev_id = step_id
    return steps


class SequentialPlanningStrategy(BasePlanningStrategy):
    strategy_id = PlanningStrategy.SEQUENTIAL

    def generate(self, context: PlanningContext) -> PlanCandidate:
        intent = _resolve_intent(context)
        templates = GOAL_TEMPLATES.get(intent, GOAL_TEMPLATES["general"])
        steps = _build_steps(templates)
        cost = sum(s.estimated_cost for s in steps)
        return PlanCandidate(
            candidate_id=str(uuid.uuid4()),
            strategy=self.strategy_id,
            steps=steps,
            estimated_cost=cost,
            score=70.0,
        )


class ParallelPlanningStrategy(BasePlanningStrategy):
    strategy_id = PlanningStrategy.PARALLEL

    def generate(self, context: PlanningContext) -> PlanCandidate:
        intent = _resolve_intent(context)
        templates = GOAL_TEMPLATES.get(intent, GOAL_TEMPLATES["general"])[:2]
        steps = _build_steps(templates, parallel_group="parallel_1")
        finalize = PlanStep(
            step_id="step_finalize",
            name="Finalize results",
            depends_on=[s.step_id for s in steps],
            estimated_cost=1.0,
        )
        steps.append(finalize)
        return PlanCandidate(
            candidate_id=str(uuid.uuid4()),
            strategy=self.strategy_id,
            steps=steps,
            estimated_cost=sum(s.estimated_cost for s in steps),
            score=75.0,
        )


class HierarchicalPlanningStrategy(BasePlanningStrategy):
    strategy_id = PlanningStrategy.HIERARCHICAL

    def generate(self, context: PlanningContext) -> PlanCandidate:
        intent = _resolve_intent(context)
        parent = PlanStep(step_id="step_parent", name=f"Goal: {context.goal[:50]}", estimated_cost=0.5)
        templates = GOAL_TEMPLATES.get(intent, GOAL_TEMPLATES["general"])
        children = _build_steps(templates)
        for child in children:
            child.depends_on = ["step_parent"]
        steps = [parent, *children]
        return PlanCandidate(
            candidate_id=str(uuid.uuid4()),
            strategy=self.strategy_id,
            steps=steps,
            estimated_cost=sum(s.estimated_cost for s in steps),
            score=80.0,
        )


class GoalDecompositionStrategy(BasePlanningStrategy):
    strategy_id = PlanningStrategy.GOAL_DECOMPOSITION

    def generate(self, context: PlanningContext) -> PlanCandidate:
        intent = _resolve_intent(context)
        subgoals = [
            PlanStep(step_id="step_decompose", name="Decompose goal", estimated_cost=0.5),
            PlanStep(step_id="step_prioritize", name="Prioritize sub-goals", depends_on=["step_decompose"], estimated_cost=0.5),
        ]
        templates = GOAL_TEMPLATES.get(intent, GOAL_TEMPLATES["general"])
        action_steps = _build_steps(templates)
        for s in action_steps:
            s.depends_on = ["step_prioritize"]
        steps = subgoals + action_steps
        return PlanCandidate(
            candidate_id=str(uuid.uuid4()),
            strategy=self.strategy_id,
            steps=steps,
            estimated_cost=sum(s.estimated_cost for s in steps),
            score=85.0,
        )


class DependencyAwarePlanningStrategy(BasePlanningStrategy):
    strategy_id = PlanningStrategy.DEPENDENCY_AWARE

    def generate(self, context: PlanningContext) -> PlanCandidate:
        seq = SequentialPlanningStrategy()
        candidate = seq.generate(context)
        candidate.strategy = self.strategy_id
        if context.available_tools:
            for step in candidate.steps:
                matching = [t for t in context.available_tools if step.capability and step.capability.split("_")[0] in t]
                if matching:
                    step.tool_id = matching[0]
        if context.agent_id:
            for step in candidate.steps:
                step.agent_id = context.agent_id
        candidate.score = 90.0
        return candidate


class AdaptiveReplanningStrategy(BasePlanningStrategy):
    strategy_id = PlanningStrategy.ADAPTIVE_REPLANNING

    def generate(self, context: PlanningContext) -> PlanCandidate:
        dep = DependencyAwarePlanningStrategy()
        candidate = dep.generate(context)
        candidate.strategy = self.strategy_id
        candidate.steps.append(
            PlanStep(
                step_id="step_monitor",
                name="Monitor and adapt",
                depends_on=[candidate.steps[-1].step_id] if candidate.steps else [],
                estimated_cost=0.5,
            )
        )
        candidate.estimated_cost = sum(s.estimated_cost for s in candidate.steps)
        candidate.score = 88.0
        return candidate


STRATEGY_REGISTRY: dict[str, BasePlanningStrategy] = {
    "sequential": SequentialPlanningStrategy(),
    "parallel": ParallelPlanningStrategy(),
    "hierarchical": HierarchicalPlanningStrategy(),
    "goal_decomposition": GoalDecompositionStrategy(),
    "dependency_aware": DependencyAwarePlanningStrategy(),
    "adaptive_replanning": AdaptiveReplanningStrategy(),
}
