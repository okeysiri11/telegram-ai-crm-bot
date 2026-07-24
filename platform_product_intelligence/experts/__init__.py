"""AI Expert Board — Sprint 22.0."""

from __future__ import annotations

from typing import Any

from platform_product_intelligence.models import EXPERT_ROLES


class ExpertBoard:
    SCORING = {
        "product": {"value": 0.82, "user_impact": 0.78, "product_impact": 0.8},
        "technical": {"complexity": 0.55, "code_impact": 0.4, "tech_debt": 0.3, "cost": 0.5},
        "ux": {"usability": 0.84, "action_count": 3, "simplicity": 0.8},
        "business": {"revenue": 0.7, "retention": 0.65, "competitive": 0.6, "commercial": 0.72},
        "security": {"security": 0.9, "privacy": 0.88, "risk": 0.25},
        "architecture": {"fit": 0.86, "compatibility": 0.9, "scalability": 0.85},
        "qa": {"tests_needed": 8, "failure_scenarios": 5, "regression_scope": "module+integration"},
    }

    def evaluate(self, *, problem: str, proposal: str) -> dict[str, Any]:
        opinions = []
        for role in EXPERT_ROLES:
            scores = dict(self.SCORING[role])
            conclusion = f"{role} AI: proposal is viable with measurable controls"
            if role == "security" and scores["risk"] > 0.7:
                conclusion = f"{role} AI: elevated risk — mitigate before approval"
            opinions.append(
                {
                    "expert": role,
                    "scores": scores,
                    "conclusion": conclusion,
                    "recommend": True,
                }
            )
        recommend_count = sum(1 for o in opinions if o["recommend"])
        return {
            "problem": problem,
            "proposal": proposal,
            "opinions": opinions,
            "consensus": recommend_count / len(opinions),
            "board_recommendation": "proceed_to_owner" if recommend_count >= 5 else "revise",
            "ai_may_modify_system": False,
        }
