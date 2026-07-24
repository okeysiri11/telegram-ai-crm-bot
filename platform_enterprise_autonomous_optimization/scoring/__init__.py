"""Optimization Scoring — Sprint 24.6."""

from __future__ import annotations

from typing import Any


class OptimizationScoring:
    def score(self, *, opportunity: dict[str, Any], complexity: float = 0.4, user_impact: float = 0.5, technical_cost: float = 0.3, strategic_value: float = 0.6) -> dict[str, Any]:
        roi = float(opportunity.get("expected_roi", 0))
        risk = float(opportunity.get("risk_score", 0.3))
        scores = {
            "roi": round(roi, 3),
            "risk": round(risk, 3),
            "complexity": float(complexity),
            "user_impact": float(user_impact),
            "technical_cost": float(technical_cost),
            "strategic_value": float(strategic_value),
        }
        # higher is better except risk/complexity/cost
        rank = round(
            scores["roi"] * 0.3
            + scores["strategic_value"] * 0.25
            + scores["user_impact"] * 0.2
            - scores["risk"] * 0.15
            - scores["complexity"] * 0.05
            - scores["technical_cost"] * 0.05,
            3,
        )
        return {"scores": scores, "rank_score": rank, "ranked": True}
