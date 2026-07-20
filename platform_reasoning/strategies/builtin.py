# Built-in reasoning strategies — no OpenAI dependency.

from __future__ import annotations

import re
import time

from platform_reasoning.models import ReasoningContext, ReasoningTrace
from platform_reasoning.strategies.base import BaseReasoningStrategy

INTENT_KEYWORDS: dict[str, list[str]] = {
    "buy_car": ["buy", "purchase", "car", "auto", "vehicle", "vin"],
    "legal_contract": ["legal", "contract", "agreement", "compliance"],
    "grain_trade": ["grain", "agro", "crop", "harvest", "freight"],
    "crm_lookup": ["crm", "customer", "lead", "client"],
    "shipment_tracking": ["shipment", "track", "port", "logistics", "cargo"],
    "market_analysis": ["market", "analysis", "report", "erp", "inventory"],
    "book_appointment": ["appointment", "book", "beauty", "salon"],
}

CONSTRAINT_PATTERNS = [
    (r"\b(urgent|asap|immediately)\b", "time_sensitive"),
    (r"\b(budget|price|cost|under \$?\d+)\b", "budget_constraint"),
    (r"\b(must|required|mandatory)\b", "hard_requirement"),
    (r"\b(confidential|private|nda)\b", "confidentiality"),
]


class RuleBasedStrategy(BaseReasoningStrategy):
    strategy_id = "rule_based"

    async def reason(self, context: ReasoningContext, trace: ReasoningTrace) -> dict:
        started = time.monotonic()
        request_lower = context.request.lower()
        intent = "general_inquiry"
        best_score = 0

        for cap, keywords in INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in request_lower)
            if score > best_score:
                best_score = score
                intent = cap

        constraints = list(context.constraints)
        for pattern, label in CONSTRAINT_PATTERNS:
            if re.search(pattern, request_lower, re.I):
                constraints.append(label)

        self._step(
            trace, "rule_match", f"Matched intent '{intent}' via keyword rules",
            input_summary=context.request[:100], output_summary=f"intent={intent}, score={best_score}",
            confidence=min(60 + best_score * 10, 95), duration_ms=(time.monotonic() - started) * 1000,
        )
        return {"intent": intent, "constraints": constraints, "confidence_boost": best_score * 5}


class ChainOfThoughtStrategy(BaseReasoningStrategy):
    strategy_id = "chain_of_thought"

    async def reason(self, context: ReasoningContext, trace: ReasoningTrace) -> dict:
        thoughts = [
            f"User request: '{context.request[:80]}'",
            f"Agent context: {context.agent_id or 'unassigned'}",
            f"Available capabilities: {', '.join(context.capabilities[:5]) or 'none'}",
            "Evaluating best approach step by step",
        ]
        for i, thought in enumerate(thoughts):
            self._step(trace, "thought", thought, confidence=50 + i * 10)

        rule = RuleBasedStrategy()
        data = await rule.reason(context, trace)
        data["reasoning_depth"] = len(thoughts)
        return data


class TreeOfThoughtStrategy(BaseReasoningStrategy):
    strategy_id = "tree_of_thought"

    async def reason(self, context: ReasoningContext, trace: ReasoningTrace) -> dict:
        branches = ["direct_execution", "gather_more_info", "delegate_to_specialist"]
        scores: dict[str, float] = {}

        for branch in branches:
            score = 50.0
            if branch == "direct_execution" and context.capabilities:
                score = 75.0
            if branch == "gather_more_info" and "?" in context.request:
                score = 80.0
            if branch == "delegate_to_specialist" and context.agent_id:
                score = 70.0
            scores[branch] = score
            self._step(trace, "branch", f"Evaluated branch '{branch}'", output_summary=f"score={score}", confidence=score)

        best_branch = max(scores, key=scores.get)
        self._step(trace, "select", f"Selected branch '{best_branch}'", confidence=scores[best_branch])

        rule = RuleBasedStrategy()
        data = await rule.reason(context, trace)
        data["selected_branch"] = best_branch
        return data


class ReflectiveStrategy(BaseReasoningStrategy):
    strategy_id = "reflective"

    async def reason(self, context: ReasoningContext, trace: ReasoningTrace) -> dict:
        cot = ChainOfThoughtStrategy()
        data = await cot.reason(context, trace)

        self._step(trace, "reflect", "Reviewing initial reasoning for gaps and contradictions")
        missing = []
        if not context.memory_context:
            missing.append("user_history")
        if "?" not in context.request and len(context.request.split()) < 5:
            missing.append("request_detail")

        reflection_conf = 85.0 if not missing else 60.0
        self._step(
            trace, "reflect_result",
            f"Reflection complete — {len(missing)} gaps found",
            output_summary=f"missing={missing}", confidence=reflection_conf,
        )
        data["missing_information"] = missing
        data["confidence_boost"] = data.get("confidence_boost", 0) + (10 if not missing else -5)
        return data


class PlanningFirstStrategy(BaseReasoningStrategy):
    strategy_id = "planning_first"

    async def reason(self, context: ReasoningContext, trace: ReasoningTrace) -> dict:
        rule = RuleBasedStrategy()
        data = await rule.reason(context, trace)
        intent = data["intent"]

        plan = ["understand_request", "validate_constraints", f"execute_{intent}", "verify_result"]
        if data.get("missing_information"):
            plan.insert(1, "gather_missing_information")

        for i, step in enumerate(plan):
            self._step(trace, "plan", f"Plan step {i + 1}: {step}", confidence=70 + i * 5)

        data["plan"] = plan
        return data


class FastHeuristicStrategy(BaseReasoningStrategy):
    strategy_id = "fast_heuristic"

    async def reason(self, context: ReasoningContext, trace: ReasoningTrace) -> dict:
        started = time.monotonic()
        request_lower = context.request.lower()

        intent = "general_inquiry"
        if context.capabilities:
            for cap in context.capabilities:
                if cap.replace("_", " ") in request_lower or any(w in request_lower for w in cap.split("_")):
                    intent = cap
                    break

        if intent == "general_inquiry":
            for cap, keywords in INTENT_KEYWORDS.items():
                if any(kw in request_lower for kw in keywords):
                    intent = cap
                    break

        self._step(
            trace, "heuristic", f"Fast match: intent={intent}",
            duration_ms=(time.monotonic() - started) * 1000, confidence=65,
        )
        return {"intent": intent, "constraints": list(context.constraints), "confidence_boost": 5}


STRATEGY_REGISTRY: dict[str, BaseReasoningStrategy] = {
    "rule_based": RuleBasedStrategy(),
    "chain_of_thought": ChainOfThoughtStrategy(),
    "tree_of_thought": TreeOfThoughtStrategy(),
    "reflective": ReflectiveStrategy(),
    "planning_first": PlanningFirstStrategy(),
    "fast_heuristic": FastHeuristicStrategy(),
}
