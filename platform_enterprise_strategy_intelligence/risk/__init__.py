"""Strategic Risk Engine — Sprint 24.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_strategy_intelligence.models import RISK_TYPES


class StrategicRiskEngine:
    def assess(self, *, scores: dict[str, float] | None = None) -> dict[str, Any]:
        scores = dict(scores or {})
        risks = []
        total = 0.0
        for rtype in RISK_TYPES:
            score = float(scores.get(rtype, 0.25))
            level = "low" if score < 0.35 else "medium" if score < 0.6 else "high"
            risks.append({"type": rtype, "score": score, "level": level})
            total += score
        avg = round(total / len(RISK_TYPES), 3)
        return {
            "risks": risks,
            "overall_risk": avg,
            "types": list(RISK_TYPES),
        }
