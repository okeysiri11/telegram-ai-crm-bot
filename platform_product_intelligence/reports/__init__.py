"""Decision report generator — Sprint 22.0."""

from __future__ import annotations

from typing import Any


class DecisionReportGenerator:
    def generate(
        self,
        *,
        problem: str,
        proposal: str,
        analysis: dict[str, Any],
        expert_board: dict[str, Any],
    ) -> dict[str, Any]:
        complexity = expert_board["opinions"][1]["scores"]["complexity"]
        cost = expert_board["opinions"][1]["scores"]["cost"]
        effect = analysis.get("forecast", {})
        priority = "P1" if analysis.get("impact") == "high" else ("P2" if analysis.get("impact") == "medium" else "P3")
        return {
            "problem": problem,
            "proposed_solution": proposal,
            "pros": [
                "addresses recurring feedback",
                "measurable KPI defined",
                "aligned with expert consensus",
            ],
            "cons": [
                "requires coordinated delivery",
                "needs post-release validation",
            ],
            "risks": [
                "scope creep without owner gate",
                "kpi miss if adoption low",
            ],
            "implementation_complexity": complexity,
            "cost": cost,
            "expected_effect": effect,
            "kpi": [
                {"name": "adoption_lift_pct", "target": effect.get("adoption_lift_pct", 0)},
                {"name": "support_ticket_reduction_pct", "target": effect.get("support_ticket_reduction_pct", 0)},
            ],
            "priority": priority,
            "expert_conclusions": [
                {"expert": o["expert"], "conclusion": o["conclusion"]} for o in expert_board["opinions"]
            ],
            "final_recommendation": expert_board["board_recommendation"],
            "ai_autonomous_change": False,
            "requires_owner_decision": True,
        }
